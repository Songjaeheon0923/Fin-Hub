"""
Consul Service Discovery Client
Handles service registration, discovery, and health checks
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin
import aiohttp
from datetime import datetime

from ..schemas.mcp_protocol import ServiceRegistration, HealthStatus


logger = logging.getLogger(__name__)


class ConsulClient:
    """Consul client for service discovery and configuration"""

    def __init__(
        self,
        consul_host: str = "localhost",
        consul_port: int = 8500,
        consul_scheme: str = "http",
        consul_token: Optional[str] = None
    ):
        self.consul_host = consul_host
        self.consul_port = consul_port
        self.consul_scheme = consul_scheme
        self.consul_token = consul_token
        self.base_url = f"{consul_scheme}://{consul_host}:{consul_port}"
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()

    async def start(self):
        """Initialize HTTP session"""
        headers = {}
        if self.consul_token:
            headers["X-Consul-Token"] = self.consul_token

        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers=headers
        )

    async def stop(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to Consul API"""
        if not self.session:
            raise RuntimeError("ConsulClient not started. Use async context manager.")

        url = urljoin(self.base_url, endpoint)

        try:
            async with self.session.request(
                method=method,
                url=url,
                json=data,
                params=params
            ) as response:
                if response.content_type == 'application/json':
                    result = await response.json()
                else:
                    result = {"text": await response.text()}

                if response.status >= 400:
                    logger.error(f"Consul API error: {response.status} - {result}")
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=response.status,
                        message=str(result)
                    )

                return result

        except aiohttp.ClientError as e:
            logger.error(f"Consul request failed: {e}")
            raise

    # Service Registration
    async def register_service(self, registration: ServiceRegistration) -> bool:
        """Register service with Consul"""
        service_data = {
            "ID": registration.service_id,
            "Name": registration.service_name,
            "Address": registration.address,
            "Port": registration.port,
            "Tags": registration.tags,
            "Meta": registration.meta
        }

        # Add health check if provided
        if registration.health_check:
            service_data["Check"] = registration.health_check

        try:
            await self._request("PUT", f"/v1/agent/service/register", data=service_data)
            logger.info(f"Service {registration.service_id} registered successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to register service {registration.service_id}: {e}")
            return False

    async def deregister_service(self, service_id: str) -> bool:
        """Deregister service from Consul"""
        try:
            await self._request("PUT", f"/v1/agent/service/deregister/{service_id}")
            logger.info(f"Service {service_id} deregistered successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to deregister service {service_id}: {e}")
            return False

    # Service Discovery
    async def discover_services(self, service_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Discover services from Consul catalog"""
        try:
            if service_name:
                endpoint = f"/v1/catalog/service/{service_name}"
            else:
                endpoint = "/v1/catalog/services"

            result = await self._request("GET", endpoint)

            if service_name:
                return result if isinstance(result, list) else []
            else:
                # Convert services dict to list format
                services = []
                for name, tags in result.items():
                    services.append({"name": name, "tags": tags})
                return services

        except Exception as e:
            logger.error(f"Failed to discover services: {e}")
            return []

    async def get_healthy_services(self, service_name: str) -> List[Dict[str, Any]]:
        """Get only healthy instances of a service"""
        try:
            result = await self._request(
                "GET",
                f"/v1/health/service/{service_name}",
                params={"passing": "true"}
            )
            return result if isinstance(result, list) else []

        except Exception as e:
            logger.error(f"Failed to get healthy services for {service_name}: {e}")
            return []

    # Health Checks
    async def check_service_health(self, service_id: str) -> HealthStatus:
        """Check health status of a specific service"""
        try:
            result = await self._request("GET", f"/v1/agent/health/service/id/{service_id}")

            # Consul health check result format
            status = "healthy"
            details = {}

            if isinstance(result, dict):
                checks = result.get("Checks", [])
                for check in checks:
                    if check.get("Status") != "passing":
                        status = "unhealthy"
                        details[check.get("CheckID", "unknown")] = {
                            "status": check.get("Status"),
                            "output": check.get("Output", "")
                        }

            return HealthStatus(
                status=status,
                timestamp=datetime.utcnow().isoformat(),
                details=details if details else None
            )

        except Exception as e:
            logger.error(f"Failed to check health for service {service_id}: {e}")
            return HealthStatus(
                status="unhealthy",
                timestamp=datetime.utcnow().isoformat(),
                details={"error": str(e)}
            )

    # Key-Value Store
    async def set_config(self, key: str, value: Any) -> bool:
        """Set configuration value in Consul KV store"""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            elif not isinstance(value, str):
                value = str(value)

            await self._request("PUT", f"/v1/kv/{key}", data=value)
            logger.debug(f"Config key {key} set successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to set config key {key}: {e}")
            return False

    async def get_config(self, key: str) -> Optional[Any]:
        """Get configuration value from Consul KV store"""
        try:
            result = await self._request("GET", f"/v1/kv/{key}")

            if isinstance(result, list) and len(result) > 0:
                value = result[0].get("Value", "")
                if value:
                    # Decode base64 value
                    import base64
                    decoded_value = base64.b64decode(value).decode('utf-8')

                    # Try to parse as JSON
                    try:
                        return json.loads(decoded_value)
                    except json.JSONDecodeError:
                        return decoded_value

            return None

        except Exception as e:
            logger.error(f"Failed to get config key {key}: {e}")
            return None

    async def delete_config(self, key: str) -> bool:
        """Delete configuration key from Consul KV store"""
        try:
            await self._request("DELETE", f"/v1/kv/{key}")
            logger.debug(f"Config key {key} deleted successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to delete config key {key}: {e}")
            return False

    # Utility Methods
    async def is_leader(self) -> bool:
        """Check if this Consul instance is the leader"""
        try:
            result = await self._request("GET", "/v1/status/leader")
            leader_address = result.strip('"') if isinstance(result, str) else ""
            current_address = f"{self.consul_host}:{self.consul_port}"
            return leader_address.endswith(current_address)

        except Exception as e:
            logger.error(f"Failed to check leader status: {e}")
            return False

    async def get_peers(self) -> List[str]:
        """Get list of Consul peers"""
        try:
            result = await self._request("GET", "/v1/status/peers")
            return result if isinstance(result, list) else []

        except Exception as e:
            logger.error(f"Failed to get peers: {e}")
            return []