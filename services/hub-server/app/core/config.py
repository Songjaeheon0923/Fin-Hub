"""
Hub Server Configuration
Extends base configuration with Hub-specific settings
"""

import os
from typing import List
from pydantic import Field

# Import shared configuration
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from shared.config.base import HubServerConfig


class HubConfig(HubServerConfig):
    """Hub Server specific configuration"""

    # Override service defaults
    service_name: str = Field(default="hub-server")
    port: int = Field(default=8000)

    # Database Configuration (required for Hub)
    database_url: str = Field(
        default="postgresql+asyncpg://fin_hub:fin_hub_pass@postgres:5432/fin_hub_registry",
        description="PostgreSQL database URL for registry"
    )

    # Hub-specific settings
    max_registered_services: int = Field(
        default=100,
        description="Maximum number of services that can be registered",
        ge=1
    )

    service_ttl_seconds: int = Field(
        default=300,  # 5 minutes
        description="Service registration TTL in seconds",
        ge=60
    )

    cleanup_interval_seconds: int = Field(
        default=60,  # 1 minute
        description="Interval for cleaning up expired services",
        ge=10
    )

    # Tool execution settings
    tool_execution_timeout: int = Field(
        default=300,  # 5 minutes
        description="Maximum tool execution timeout in seconds",
        ge=1
    )

    max_concurrent_executions: int = Field(
        default=10,
        description="Maximum concurrent tool executions",
        ge=1
    )

    execution_queue_size: int = Field(
        default=100,
        description="Maximum execution queue size",
        ge=1
    )

    # Load balancing settings
    load_balancer_algorithm: str = Field(
        default="round_robin",
        description="Load balancing algorithm (round_robin, least_connections, weighted)"
    )

    health_check_timeout: int = Field(
        default=10,
        description="Health check timeout in seconds",
        ge=1
    )

    unhealthy_threshold: int = Field(
        default=3,
        description="Number of failed health checks before marking service unhealthy",
        ge=1
    )

    # MCP Server settings
    mcp_server_name: str = Field(default="fin-hub-registry")
    mcp_server_version: str = Field(default="1.0.0")

    # API Documentation
    enable_api_docs: bool = Field(
        default=True,
        description="Enable API documentation endpoints"
    )

    docs_url: str = Field(
        default="/docs",
        description="API documentation URL"
    )

    redoc_url: str = Field(
        default="/redoc",
        description="ReDoc documentation URL"
    )

    # CORS settings
    cors_enabled: bool = Field(
        default=True,
        description="Enable CORS middleware"
    )

    cors_origins: List[str] = Field(
        default=["*"],
        description="Allowed CORS origins"
    )

    cors_methods: List[str] = Field(
        default=["*"],
        description="Allowed CORS methods"
    )

    cors_headers: List[str] = Field(
        default=["*"],
        description="Allowed CORS headers"
    )

    class Config:
        env_prefix = "HUB_"
        env_file = ".env"


# Global config instance
_config: HubConfig = None


def get_config() -> HubConfig:
    """Get global configuration instance"""
    global _config
    if _config is None:
        _config = HubConfig()
    return _config


def reload_config():
    """Reload configuration (useful for testing)"""
    global _config
    _config = HubConfig()