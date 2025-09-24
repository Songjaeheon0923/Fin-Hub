"""
Service Registry and Discovery Service
Manages service registration, health checking, and load balancing
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from sqlalchemy import select, update, delete, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from shared.schemas.mcp_protocol import ServiceRegistration, HealthStatus
from shared.utils.logging import LoggerMixin
from shared.utils.consul_client import ConsulClient

from ..core.config import get_config
from ..core.database import get_session
from ..models.registry import Service
from ..models.tools import Tool


@dataclass
class ServiceInstance:
    """Service instance data"""
    service: Service
    tools: List[Tool]
    last_health_check: Optional[datetime] = None
    health_status: Optional[HealthStatus] = None


class RegistryService(LoggerMixin):
    """Service registry and discovery implementation"""

    def __init__(self):
        self.config = get_config()
        self.consul_client: Optional[ConsulClient] = None
        self._health_check_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self):
        """Start registry service"""
        if self._running:
            return

        self._running = True

        # Initialize Consul client
        try:
            consul_config = self.config.get_consul_config()
            self.consul_client = ConsulClient(
                consul_host=consul_config["host"],
                consul_port=consul_config["port"],
                consul_token=consul_config.get("token")
            )
            await self.consul_client.start()
            self.logger.info("Connected to Consul")

        except Exception as e:
            self.logger.warning(f"Failed to connect to Consul: {e}")
            self.consul_client = None

        # Start background tasks
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

        self.logger.info("Registry service started")

    async def stop(self):
        """Stop registry service"""
        self._running = False

        # Cancel background tasks
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        # Close Consul client
        if self.consul_client:
            await self.consul_client.stop()

        self.logger.info("Registry service stopped")

    async def register_service(
        self,
        registration: ServiceRegistration,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Register a service with the hub

        Args:
            registration: Service registration information
            tools: Optional list of tools provided by the service

        Returns:
            True if registration successful
        """
        try:
            async with get_session() as session:
                # Check if service already exists
                existing_service = await session.execute(
                    select(Service).where(Service.service_id == registration.service_id)
                )
                service = existing_service.scalar_one_or_none()

                if service:
                    # Update existing service
                    service.address = registration.address
                    service.port = registration.port
                    service.tags = registration.tags
                    service.meta = registration.meta
                    service.update_last_seen()
                    service.is_active = True
                    service.consecutive_failures = 0

                    self.logger.info(f"Updated existing service: {registration.service_id}")
                else:
                    # Create new service
                    service = Service(
                        service_id=registration.service_id,
                        service_name=registration.service_name,
                        address=registration.address,
                        port=registration.port,
                        tags=registration.tags,
                        meta=registration.meta,
                        health_check_url=registration.health_check.get("http") if registration.health_check else None,
                        health_check_interval=registration.health_check.get("interval", 30) if registration.health_check else 30,
                        ttl_seconds=self.config.service_ttl_seconds
                    )
                    session.add(service)
                    await session.flush()  # Get the ID

                    self.logger.info(f"Registered new service: {registration.service_id}")

                # Register tools if provided
                if tools:
                    await self._register_service_tools(session, service, tools)

                await session.commit()

                # Register with Consul if available
                if self.consul_client:
                    await self._register_with_consul(registration)

                return True

        except Exception as e:
            self.logger.error(f"Failed to register service {registration.service_id}: {e}")
            return False

    async def deregister_service(self, service_id: str) -> bool:
        """
        Deregister a service

        Args:
            service_id: Service identifier

        Returns:
            True if deregistration successful
        """
        try:
            async with get_session() as session:
                # Mark service as inactive
                await session.execute(
                    update(Service)
                    .where(Service.service_id == service_id)
                    .values(is_active=False)
                )
                await session.commit()

                # Deregister from Consul
                if self.consul_client:
                    await self.consul_client.deregister_service(service_id)

                self.logger.info(f"Deregistered service: {service_id}")
                return True

        except Exception as e:
            self.logger.error(f"Failed to deregister service {service_id}: {e}")
            return False

    async def get_service(self, service_id: str) -> Optional[ServiceInstance]:
        """Get service by ID"""
        try:
            async with get_session() as session:
                # Get service with tools
                result = await session.execute(
                    select(Service, Tool)
                    .outerjoin(Tool)
                    .where(
                        and_(
                            Service.service_id == service_id,
                            Service.is_active == True
                        )
                    )
                )

                rows = result.fetchall()
                if not rows:
                    return None

                # Group tools by service
                service = rows[0][0]
                tools = [row[1] for row in rows if row[1] is not None]

                return ServiceInstance(
                    service=service,
                    tools=tools
                )

        except Exception as e:
            self.logger.error(f"Failed to get service {service_id}: {e}")
            return None

    async def discover_services(
        self,
        service_name: Optional[str] = None,
        tags: Optional[List[str]] = None,
        healthy_only: bool = True
    ) -> List[ServiceInstance]:
        """
        Discover services

        Args:
            service_name: Filter by service name
            tags: Filter by tags (any match)
            healthy_only: Only return healthy services

        Returns:
            List of matching services
        """
        try:
            async with get_session() as session:
                # Build query conditions
                conditions = [Service.is_active == True]

                if service_name:
                    conditions.append(Service.service_name == service_name)

                if healthy_only:
                    conditions.append(Service.is_healthy == True)

                if tags:
                    # PostgreSQL JSON contains any of the tags
                    tag_conditions = []
                    for tag in tags:
                        tag_conditions.append(Service.tags.contains([tag]))
                    conditions.append(or_(*tag_conditions))

                # Execute query
                result = await session.execute(
                    select(Service, Tool)
                    .outerjoin(Tool)
                    .where(and_(*conditions))
                    .order_by(Service.service_name, Service.service_id)
                )

                rows = result.fetchall()

                # Group by service
                services_dict = {}
                for row in rows:
                    service, tool = row
                    if service.service_id not in services_dict:
                        services_dict[service.service_id] = ServiceInstance(
                            service=service,
                            tools=[]
                        )
                    if tool:
                        services_dict[service.service_id].tools.append(tool)

                return list(services_dict.values())

        except Exception as e:
            self.logger.error(f"Failed to discover services: {e}")
            return []

    async def get_all_tools(self) -> List[Tool]:
        """Get all available tools from active services"""
        try:
            async with get_session() as session:
                result = await session.execute(
                    select(Tool)
                    .join(Service)
                    .where(
                        and_(
                            Service.is_active == True,
                            Service.is_healthy == True,
                            Tool.is_enabled == True
                        )
                    )
                    .order_by(Tool.category, Tool.tool_id)
                )

                return result.scalars().all()

        except Exception as e:
            self.logger.error(f"Failed to get all tools: {e}")
            return []

    async def get_tool(self, tool_id: str) -> Optional[Tool]:
        """Get specific tool by ID"""
        try:
            async with get_session() as session:
                result = await session.execute(
                    select(Tool)
                    .join(Service)
                    .where(
                        and_(
                            Tool.tool_id == tool_id,
                            Service.is_active == True,
                            Service.is_healthy == True,
                            Tool.is_enabled == True
                        )
                    )
                )

                return result.scalar_one_or_none()

        except Exception as e:
            self.logger.error(f"Failed to get tool {tool_id}: {e}")
            return None

    async def get_services_for_tool(self, tool_id: str) -> List[Service]:
        """Get all healthy services that provide a specific tool"""
        try:
            async with get_session() as session:
                result = await session.execute(
                    select(Service)
                    .join(Tool)
                    .where(
                        and_(
                            Tool.tool_id == tool_id,
                            Service.is_active == True,
                            Service.is_healthy == True,
                            Tool.is_enabled == True
                        )
                    )
                    .order_by(Service.weight.desc(), Service.current_load.asc())
                )

                return result.scalars().all()

        except Exception as e:
            self.logger.error(f"Failed to get services for tool {tool_id}: {e}")
            return []

    async def _register_service_tools(
        self,
        session: AsyncSession,
        service: Service,
        tools_data: List[Dict[str, Any]]
    ):
        """Register tools for a service"""
        # Remove existing tools
        await session.execute(
            delete(Tool).where(Tool.service_id == service.id)
        )

        # Add new tools
        for tool_data in tools_data:
            tool = Tool(
                service_id=service.id,
                tool_id=tool_data["name"],
                name=tool_data.get("display_name", tool_data["name"]),
                description=tool_data["description"],
                category=tool_data.get("category", "unknown"),
                version=tool_data.get("version", "1.0.0"),
                tags=tool_data.get("tags", []),
                input_schema=tool_data["input_schema"],
                output_schema=tool_data.get("output_schema"),
                timeout_seconds=tool_data.get("timeout_seconds", self.config.tool_execution_timeout)
            )
            session.add(tool)

        self.logger.info(f"Registered {len(tools_data)} tools for service {service.service_id}")

    async def _register_with_consul(self, registration: ServiceRegistration):
        """Register service with Consul"""
        try:
            await self.consul_client.register_service(registration)
        except Exception as e:
            self.logger.warning(f"Failed to register with Consul: {e}")

    async def _health_check_loop(self):
        """Background task for health checking services"""
        while self._running:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self.config.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(10)  # Short delay before retry

    async def _cleanup_loop(self):
        """Background task for cleaning up expired services"""
        while self._running:
            try:
                await self._cleanup_expired_services()
                await asyncio.sleep(self.config.cleanup_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(30)  # Longer delay before retry

    async def _perform_health_checks(self):
        """Perform health checks on all active services"""
        try:
            async with get_session() as session:
                # Get all active services that need health checking
                result = await session.execute(
                    select(Service).where(
                        and_(
                            Service.is_active == True,
                            Service.health_check_url.isnot(None),
                            or_(
                                Service.last_health_check.is_(None),
                                Service.last_health_check < datetime.now(timezone.utc) -
                                timedelta(seconds=Service.health_check_interval)
                            )
                        )
                    )
                )

                services = result.scalars().all()

                # Check each service
                for service in services:
                    await self._check_service_health(session, service)

                await session.commit()

        except Exception as e:
            self.logger.error(f"Error performing health checks: {e}")

    async def _check_service_health(self, session: AsyncSession, service: Service):
        """Check health of a single service"""
        try:
            import aiohttp
            import asyncio

            async with aiohttp.ClientSession() as http_session:
                async with asyncio.timeout(self.config.health_check_timeout):
                    async with http_session.get(service.health_check_url) as response:
                        is_healthy = response.status == 200

            service.update_health_status(is_healthy)

            if is_healthy:
                self.logger.debug(f"Service {service.service_id} is healthy")
            else:
                self.logger.warning(f"Service {service.service_id} failed health check")

                # Deactivate service if too many failures
                if service.consecutive_failures >= self.config.unhealthy_threshold:
                    service.is_active = False
                    self.logger.warning(f"Service {service.service_id} deactivated due to health failures")

        except Exception as e:
            self.logger.warning(f"Health check failed for {service.service_id}: {e}")
            service.update_health_status(False)

            if service.consecutive_failures >= self.config.unhealthy_threshold:
                service.is_active = False

    async def _cleanup_expired_services(self):
        """Clean up expired and inactive services"""
        try:
            async with get_session() as session:
                # Find expired services
                expired_time = datetime.now(timezone.utc) - \
                              timedelta(seconds=self.config.service_ttl_seconds)

                result = await session.execute(
                    select(Service).where(
                        and_(
                            Service.is_active == True,
                            Service.last_seen < expired_time
                        )
                    )
                )

                expired_services = result.scalars().all()

                # Mark as inactive
                for service in expired_services:
                    service.is_active = False
                    self.logger.info(f"Service {service.service_id} expired and deactivated")

                await session.commit()

                if expired_services:
                    self.logger.info(f"Cleaned up {len(expired_services)} expired services")

        except Exception as e:
            self.logger.error(f"Error cleaning up expired services: {e}")