"""
Tool Execution Service
Handles tool execution, load balancing, and request routing
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

import aiohttp
from sqlalchemy.ext.asyncio import AsyncSession

from shared.schemas.mcp_protocol import ToolCallRequest, ToolCallResponse
from shared.utils.logging import LoggerMixin, get_correlation_id

from ..core.config import get_config
from ..core.database import get_session
from ..models.registry import Service
from ..models.tools import Tool, ToolExecution
from .registry_service import RegistryService


class CircuitBreaker:
    """Circuit breaker for service calls"""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def can_execute(self) -> bool:
        """Check if execution is allowed"""
        if self.state == "CLOSED":
            return True
        elif self.state == "OPEN":
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = "HALF_OPEN"
                return True
            return False
        elif self.state == "HALF_OPEN":
            return True
        return False

    def record_success(self):
        """Record successful execution"""
        self.failure_count = 0
        self.state = "CLOSED"
        self.last_failure_time = None

    def record_failure(self):
        """Record failed execution"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"


class LoadBalancer:
    """Load balancer for service selection"""

    @staticmethod
    def weighted_round_robin(services: List[Service]) -> Optional[Service]:
        """Select service using weighted round-robin"""
        if not services:
            return None

        # Sort by weight (desc) and current load (asc)
        sorted_services = sorted(
            services,
            key=lambda s: (-s.weight, s.current_load)
        )

        return sorted_services[0]

    @staticmethod
    def least_connections(services: List[Service]) -> Optional[Service]:
        """Select service with least connections"""
        if not services:
            return None

        return min(services, key=lambda s: s.current_load)


class ExecutionService(LoggerMixin):
    """Tool execution and routing service"""

    def __init__(self, registry_service: RegistryService):
        self.registry_service = registry_service
        self.config = get_config()
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.active_executions: Dict[str, asyncio.Task] = {}

    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        correlation_id: Optional[str] = None,
        timeout_seconds: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute a tool with load balancing and error handling

        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments
            correlation_id: Request correlation ID
            timeout_seconds: Custom timeout (overrides tool default)

        Returns:
            Execution result
        """
        execution_id = str(uuid.uuid4())
        correlation_id = correlation_id or get_correlation_id() or str(uuid.uuid4())

        self.logger.info(
            f"Starting tool execution: {tool_name}",
            extra={
                "execution_id": execution_id,
                "correlation_id": correlation_id,
                "tool_name": tool_name
            }
        )

        try:
            # Get tool and available services
            tool = await self.registry_service.get_tool(tool_name)
            if not tool:
                return {
                    "success": False,
                    "error": f"Tool '{tool_name}' not found",
                    "error_type": "TOOL_NOT_FOUND"
                }

            services = await self.registry_service.get_services_for_tool(tool_name)
            if not services:
                return {
                    "success": False,
                    "error": f"No healthy services available for tool '{tool_name}'",
                    "error_type": "NO_SERVICES_AVAILABLE"
                }

            # Select service using load balancing
            selected_service = LoadBalancer.weighted_round_robin(services)
            if not selected_service:
                return {
                    "success": False,
                    "error": "Load balancer failed to select service",
                    "error_type": "LOAD_BALANCER_ERROR"
                }

            # Check circuit breaker
            circuit_breaker = self._get_circuit_breaker(selected_service.service_id)
            if not circuit_breaker.can_execute():
                return {
                    "success": False,
                    "error": f"Circuit breaker OPEN for service '{selected_service.service_id}'",
                    "error_type": "CIRCUIT_BREAKER_OPEN"
                }

            # Create execution record
            execution = await self._create_execution_record(
                execution_id,
                correlation_id,
                tool_name,
                selected_service.service_id,
                arguments
            )

            # Execute with timeout
            timeout = timeout_seconds or tool.timeout_seconds
            try:
                async with asyncio.timeout(timeout):
                    result = await self._execute_on_service(
                        selected_service,
                        tool,
                        arguments,
                        execution_id,
                        correlation_id
                    )

                # Record success
                circuit_breaker.record_success()
                await self._complete_execution(execution, result)
                await self._update_tool_stats(tool, True, result.get("duration_ms", 0))

                self.logger.info(
                    f"Tool execution completed successfully: {tool_name}",
                    extra={
                        "execution_id": execution_id,
                        "correlation_id": correlation_id,
                        "service_id": selected_service.service_id
                    }
                )

                return {
                    "success": True,
                    "result": result.get("data"),
                    "execution_id": execution_id,
                    "service_id": selected_service.service_id,
                    "duration_ms": result.get("duration_ms")
                }

            except asyncio.TimeoutError:
                error_data = {"error": "Tool execution timeout", "timeout_seconds": timeout}
                circuit_breaker.record_failure()
                await self._fail_execution(execution, error_data, "timeout")
                await self._update_tool_stats(tool, False, timeout * 1000)

                return {
                    "success": False,
                    "error": f"Tool execution timeout after {timeout} seconds",
                    "error_type": "TIMEOUT",
                    "execution_id": execution_id
                }

        except Exception as e:
            self.logger.error(
                f"Tool execution failed: {tool_name}",
                exc_info=e,
                extra={
                    "execution_id": execution_id,
                    "correlation_id": correlation_id,
                    "tool_name": tool_name
                }
            )

            return {
                "success": False,
                "error": f"Internal execution error: {str(e)}",
                "error_type": "INTERNAL_ERROR",
                "execution_id": execution_id
            }

    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel ongoing execution"""
        if execution_id in self.active_executions:
            task = self.active_executions[execution_id]
            task.cancel()
            del self.active_executions[execution_id]

            # Update execution record
            async with get_session() as session:
                result = await session.execute(
                    select(ToolExecution).where(
                        ToolExecution.execution_id == execution_id
                    )
                )
                execution = result.scalar_one_or_none()
                if execution:
                    execution.status = "cancelled"
                    execution.completed_at = datetime.now(timezone.utc)
                    await session.commit()

            self.logger.info(f"Execution cancelled: {execution_id}")
            return True

        return False

    async def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get execution status"""
        try:
            async with get_session() as session:
                result = await session.execute(
                    select(ToolExecution).where(
                        ToolExecution.execution_id == execution_id
                    )
                )
                execution = result.scalar_one_or_none()

                if execution:
                    return execution.to_dict()

                return None

        except Exception as e:
            self.logger.error(f"Failed to get execution status: {e}")
            return None

    def _get_circuit_breaker(self, service_id: str) -> CircuitBreaker:
        """Get or create circuit breaker for service"""
        if service_id not in self.circuit_breakers:
            self.circuit_breakers[service_id] = CircuitBreaker(
                failure_threshold=self.config.circuit_breaker_failure_threshold,
                recovery_timeout=self.config.circuit_breaker_recovery_timeout
            )
        return self.circuit_breakers[service_id]

    async def _execute_on_service(
        self,
        service: Service,
        tool: Tool,
        arguments: Dict[str, Any],
        execution_id: str,
        correlation_id: str
    ) -> Dict[str, Any]:
        """Execute tool on specific service"""
        start_time = time.time()

        # Build MCP request
        mcp_request = {
            "jsonrpc": "2.0",
            "id": execution_id,
            "method": "tools/call",
            "params": {
                "name": tool.tool_id,
                "arguments": arguments
            }
        }

        # Service URL
        service_url = f"{service.service_url}/mcp"

        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Content-Type": "application/json",
                    "X-Correlation-ID": correlation_id,
                    "X-Execution-ID": execution_id
                }

                async with session.post(
                    service_url,
                    json=mcp_request,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=tool.timeout_seconds)
                ) as response:

                    duration_ms = (time.time() - start_time) * 1000

                    if response.status == 200:
                        result_data = await response.json()
                        return {
                            "data": result_data.get("result"),
                            "duration_ms": duration_ms,
                            "status": "success"
                        }
                    else:
                        error_data = await response.text()
                        raise Exception(f"Service returned {response.status}: {error_data}")

        except aiohttp.ClientError as e:
            duration_ms = (time.time() - start_time) * 1000
            raise Exception(f"Service communication error: {str(e)}")

    async def _create_execution_record(
        self,
        execution_id: str,
        correlation_id: str,
        tool_id: str,
        service_id: str,
        input_data: Dict[str, Any]
    ) -> ToolExecution:
        """Create execution record in database"""
        try:
            async with get_session() as session:
                execution = ToolExecution(
                    execution_id=execution_id,
                    correlation_id=correlation_id,
                    tool_id=tool_id,
                    service_id=service_id,
                    input_data=input_data,
                    status="running"
                )

                session.add(execution)
                await session.commit()

                return execution

        except Exception as e:
            self.logger.error(f"Failed to create execution record: {e}")
            raise

    async def _complete_execution(
        self,
        execution: ToolExecution,
        result: Dict[str, Any]
    ):
        """Mark execution as completed"""
        try:
            async with get_session() as session:
                # Re-attach to session
                await session.merge(execution)

                execution.complete_execution(
                    output_data=result,
                    status="completed"
                )

                await session.commit()

        except Exception as e:
            self.logger.error(f"Failed to complete execution: {e}")

    async def _fail_execution(
        self,
        execution: ToolExecution,
        error_data: Dict[str, Any],
        status: str = "failed"
    ):
        """Mark execution as failed"""
        try:
            async with get_session() as session:
                # Re-attach to session
                await session.merge(execution)

                execution.fail_execution(
                    error_data=error_data,
                    status=status
                )

                await session.commit()

        except Exception as e:
            self.logger.error(f"Failed to record execution failure: {e}")

    async def _update_tool_stats(
        self,
        tool: Tool,
        success: bool,
        duration_ms: float
    ):
        """Update tool execution statistics"""
        try:
            async with get_session() as session:
                # Re-attach to session
                await session.merge(tool)

                tool.update_execution_stats(success, duration_ms)
                await session.commit()

        except Exception as e:
            self.logger.error(f"Failed to update tool stats: {e}")