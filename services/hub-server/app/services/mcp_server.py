"""
MCP (Model Context Protocol) Server Implementation
Handles MCP protocol communication with AI agents
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Callable, Awaitable
from contextlib import asynccontextmanager

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from shared.schemas.mcp_protocol import (
    MCPRequest, MCPResponse, MCPNotification, MCPError, MCPErrorCode,
    InitializeRequest, InitializeResponse, ServerCapabilities, ServerInfo,
    Tool, ToolsListResponse, ToolCallRequest, ToolCallResponse, ToolResult
)
from shared.utils.logging import LoggerMixin, get_correlation_id, set_correlation_id

from ..core.config import get_config
from .registry_service import RegistryService
from .execution_service import ExecutionService

logger = logging.getLogger(__name__)


class MCPServerCapabilities:
    """MCP Server capabilities for Fin-Hub"""

    @staticmethod
    def get_capabilities() -> ServerCapabilities:
        """Get server capabilities"""
        return ServerCapabilities(
            tools={
                "listChanged": True,  # Server can notify about tool list changes
                "callTool": True      # Server can execute tools
            },
            resources=None,  # Not implemented yet
            prompts=None,    # Not implemented yet
            logging={
                "level": "info"
            }
        )

    @staticmethod
    def get_server_info() -> ServerInfo:
        """Get server information"""
        config = get_config()
        return ServerInfo(
            name=config.mcp_server_name,
            version=config.mcp_server_version,
            protocol_version=config.mcp_protocol_version
        )


class MCPProtocolHandler(LoggerMixin):
    """Handles MCP protocol messages and routing"""

    def __init__(
        self,
        registry_service: RegistryService,
        execution_service: ExecutionService
    ):
        self.registry_service = registry_service
        self.execution_service = execution_service
        self.config = get_config()

        # Method handlers mapping
        self.handlers: Dict[str, Callable[[Dict[str, Any]], Awaitable[Any]]] = {
            # Initialization
            "initialize": self._handle_initialize,

            # Tool operations
            "tools/list": self._handle_tools_list,
            "tools/call": self._handle_tool_call,

            # Resource operations (placeholder)
            "resources/list": self._handle_resources_list,
            "resources/read": self._handle_resource_read,

            # Ping/connectivity
            "ping": self._handle_ping,
        }

        # Notification handlers
        self.notification_handlers: Dict[str, Callable[[Dict[str, Any]], Awaitable[None]]] = {
            "notifications/initialized": self._handle_initialized_notification,
            "notifications/cancelled": self._handle_cancelled_notification,
        }

    async def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle incoming MCP request

        Args:
            request_data: Raw request data

        Returns:
            Response data
        """
        try:
            # Parse request
            if "method" not in request_data:
                return self._create_error_response(
                    request_data.get("id"),
                    MCPErrorCode.INVALID_REQUEST,
                    "Missing method field"
                )

            method = request_data["method"]
            request_id = request_data.get("id")
            params = request_data.get("params", {})

            # Set correlation ID for logging
            correlation_id = get_correlation_id() or str(uuid.uuid4())
            set_correlation_id(correlation_id)

            self.logger.info(
                f"Handling MCP request: {method}",
                extra={"method": method, "request_id": request_id, "correlation_id": correlation_id}
            )

            # Handle notifications (no response expected)
            if request_id is None:
                await self._handle_notification(method, params)
                return None

            # Handle requests (response expected)
            if method in self.handlers:
                try:
                    result = await self.handlers[method](params)
                    response = MCPResponse(id=request_id, result=result)
                    return response.dict(exclude_none=True)

                except Exception as e:
                    self.logger.error(
                        f"Error handling method {method}",
                        exc_info=e,
                        extra={"method": method, "request_id": request_id}
                    )
                    return self._create_error_response(
                        request_id,
                        MCPErrorCode.INTERNAL_ERROR,
                        f"Internal error: {str(e)}"
                    )
            else:
                return self._create_error_response(
                    request_id,
                    MCPErrorCode.METHOD_NOT_FOUND,
                    f"Method '{method}' not found"
                )

        except json.JSONDecodeError as e:
            return self._create_error_response(
                None,
                MCPErrorCode.PARSE_ERROR,
                f"Invalid JSON: {str(e)}"
            )
        except Exception as e:
            self.logger.error("Unexpected error handling MCP request", exc_info=e)
            return self._create_error_response(
                None,
                MCPErrorCode.INTERNAL_ERROR,
                f"Unexpected error: {str(e)}"
            )

    async def _handle_notification(self, method: str, params: Dict[str, Any]):
        """Handle MCP notification (no response)"""
        if method in self.notification_handlers:
            try:
                await self.notification_handlers[method](params)
            except Exception as e:
                self.logger.error(
                    f"Error handling notification {method}",
                    exc_info=e,
                    extra={"method": method}
                )
        else:
            self.logger.warning(f"Unknown notification method: {method}")

    def _create_error_response(
        self,
        request_id: Optional[str],
        code: MCPErrorCode,
        message: str,
        data: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Create standardized error response"""
        error = MCPError(code=code, message=message, data=data)
        response = MCPResponse(id=request_id, error=error.dict())
        return response.dict(exclude_none=True)

    # Request Handlers
    async def _handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialize request"""
        try:
            # Validate initialize request
            init_request = InitializeRequest(**params)

            # Check protocol version compatibility
            if init_request.protocol_version != self.config.mcp_protocol_version:
                self.logger.warning(
                    f"Protocol version mismatch: client={init_request.protocol_version}, "
                    f"server={self.config.mcp_protocol_version}"
                )

            # Create response
            response = InitializeResponse(
                protocol_version=self.config.mcp_protocol_version,
                capabilities=MCPServerCapabilities.get_capabilities(),
                server_info=MCPServerCapabilities.get_server_info()
            )

            self.logger.info(
                "Client initialized successfully",
                extra={
                    "client_protocol_version": init_request.protocol_version,
                    "client_capabilities": init_request.capabilities,
                    "client_info": init_request.client_info
                }
            )

            return response.dict()

        except Exception as e:
            raise ValueError(f"Invalid initialize request: {str(e)}")

    async def _handle_tools_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/list request"""
        try:
            # Get all available tools from registry
            tools = await self.registry_service.get_all_tools()

            # Convert to MCP tool format
            mcp_tools = []
            for tool in tools:
                mcp_tool = Tool(
                    name=tool.tool_id,
                    description=tool.description,
                    input_schema=tool.input_schema
                )
                mcp_tools.append(mcp_tool)

            response = ToolsListResponse(tools=mcp_tools)
            return response.dict()

        except Exception as e:
            raise ValueError(f"Failed to list tools: {str(e)}")

    async def _handle_tool_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call request"""
        try:
            # Validate tool call request
            call_request = ToolCallRequest(**params)

            # Execute tool through execution service
            result = await self.execution_service.execute_tool(
                tool_name=call_request.name,
                arguments=call_request.arguments,
                correlation_id=get_correlation_id()
            )

            # Convert to MCP format
            if result.get("success", False):
                tool_result = ToolResult(
                    content=[{
                        "type": "text",
                        "text": json.dumps(result.get("result", {}), indent=2)
                    }],
                    is_error=False
                )
            else:
                tool_result = ToolResult(
                    content=[{
                        "type": "text",
                        "text": f"Tool execution failed: {result.get('error', 'Unknown error')}"
                    }],
                    is_error=True
                )

            response = ToolCallResponse(result=tool_result)
            return response.dict()

        except Exception as e:
            raise ValueError(f"Failed to execute tool: {str(e)}")

    async def _handle_resources_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/list request (placeholder)"""
        # Resources not implemented yet
        return {"resources": []}

    async def _handle_resource_read(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/read request (placeholder)"""
        # Resources not implemented yet
        raise ValueError("Resources not implemented")

    async def _handle_ping(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle ping request"""
        return {
            "status": "pong",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "server": MCPServerCapabilities.get_server_info().dict()
        }

    # Notification Handlers
    async def _handle_initialized_notification(self, params: Dict[str, Any]):
        """Handle initialized notification"""
        self.logger.info("Client initialization completed")

    async def _handle_cancelled_notification(self, params: Dict[str, Any]):
        """Handle cancelled notification"""
        request_id = params.get("requestId")
        if request_id:
            # Cancel ongoing execution if possible
            await self.execution_service.cancel_execution(request_id)
            self.logger.info(f"Execution cancelled: {request_id}")


class MCPServer(LoggerMixin):
    """Main MCP Server class"""

    def __init__(
        self,
        registry_service: RegistryService,
        execution_service: ExecutionService
    ):
        self.protocol_handler = MCPProtocolHandler(registry_service, execution_service)
        self.config = get_config()
        self.is_running = False

    async def handle_message(self, message: str) -> Optional[str]:
        """
        Handle incoming MCP message

        Args:
            message: JSON-encoded MCP message

        Returns:
            JSON-encoded response or None for notifications
        """
        try:
            # Parse message
            message_data = json.loads(message)

            # Handle request
            response_data = await self.protocol_handler.handle_request(message_data)

            # Return response if not None (notifications return None)
            if response_data is not None:
                return json.dumps(response_data, default=str)

            return None

        except Exception as e:
            self.logger.error(f"Error handling MCP message: {e}", exc_info=e)
            # Return error response
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": MCPErrorCode.INTERNAL_ERROR.value,
                    "message": f"Message handling error: {str(e)}"
                }
            }
            return json.dumps(error_response)

    async def start(self):
        """Start MCP server"""
        self.is_running = True
        self.logger.info(f"MCP Server started: {self.config.mcp_server_name} v{self.config.mcp_server_version}")

    async def stop(self):
        """Stop MCP server"""
        self.is_running = False
        self.logger.info("MCP Server stopped")

    @asynccontextmanager
    async def lifespan_manager(self):
        """Async context manager for server lifespan"""
        await self.start()
        try:
            yield self
        finally:
            await self.stop()