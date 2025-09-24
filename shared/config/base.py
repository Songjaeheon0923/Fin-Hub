"""
Base Configuration Classes for Fin-Hub Services
Provides common configuration patterns and validation
"""

import os
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from pydantic import Field, validator
from pydantic_settings import BaseSettings
from enum import Enum


class Environment(str, Enum):
    """Environment types"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    """Logging levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogFormat(str, Enum):
    """Log formats"""
    JSON = "json"
    TEXT = "text"


class BaseConfig(BaseSettings):
    """Base configuration class for all Fin-Hub services"""

    # Environment
    environment: Environment = Field(
        default=Environment.DEVELOPMENT,
        description="Application environment"
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )

    # Service Info
    service_name: str = Field(
        default="fin-hub-service",
        description="Service name for logging and identification"
    )
    service_version: str = Field(
        default="1.0.0",
        description="Service version"
    )
    api_prefix: str = Field(
        default="/api/v1",
        description="API prefix for routes"
    )

    # Server Configuration
    host: str = Field(
        default="0.0.0.0",
        description="Server host"
    )
    port: int = Field(
        default=8000,
        description="Server port",
        ge=1,
        le=65535
    )
    workers: int = Field(
        default=1,
        description="Number of worker processes",
        ge=1
    )

    # Database Configuration
    database_url: Optional[str] = Field(
        default=None,
        description="Database connection URL"
    )
    db_pool_size: int = Field(
        default=10,
        description="Database connection pool size",
        ge=1
    )
    db_pool_overflow: int = Field(
        default=20,
        description="Database connection pool overflow",
        ge=0
    )

    # Redis Configuration
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    redis_pool_size: int = Field(
        default=10,
        description="Redis connection pool size",
        ge=1
    )

    # Consul Configuration
    consul_host: str = Field(
        default="localhost",
        description="Consul server host"
    )
    consul_port: int = Field(
        default=8500,
        description="Consul server port",
        ge=1,
        le=65535
    )
    consul_token: Optional[str] = Field(
        default=None,
        description="Consul access token"
    )
    consul_datacenter: str = Field(
        default="dc1",
        description="Consul datacenter"
    )

    # Logging Configuration
    log_level: LogLevel = Field(
        default=LogLevel.INFO,
        description="Logging level"
    )
    log_format: LogFormat = Field(
        default=LogFormat.JSON,
        description="Log format"
    )
    log_file_path: Optional[str] = Field(
        default=None,
        description="Log file path"
    )

    # Security Configuration
    secret_key: str = Field(
        default="change-this-secret-key-in-production",
        description="Secret key for encryption and signing",
        min_length=32
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT signing algorithm"
    )
    jwt_expire_minutes: int = Field(
        default=1440,  # 24 hours
        description="JWT expiration time in minutes",
        ge=1
    )

    # Rate Limiting
    rate_limit_enabled: bool = Field(
        default=True,
        description="Enable rate limiting"
    )
    rate_limit_requests_per_minute: int = Field(
        default=60,
        description="Rate limit requests per minute",
        ge=1
    )

    # Circuit Breaker
    circuit_breaker_enabled: bool = Field(
        default=True,
        description="Enable circuit breaker pattern"
    )
    circuit_breaker_failure_threshold: int = Field(
        default=5,
        description="Circuit breaker failure threshold",
        ge=1
    )
    circuit_breaker_recovery_timeout: int = Field(
        default=60,
        description="Circuit breaker recovery timeout in seconds",
        ge=1
    )

    # Caching
    cache_ttl: int = Field(
        default=300,  # 5 minutes
        description="Default cache TTL in seconds",
        ge=0
    )
    cache_max_size: int = Field(
        default=1000,
        description="Maximum cache size",
        ge=1
    )

    # Monitoring
    metrics_enabled: bool = Field(
        default=True,
        description="Enable metrics collection"
    )
    prometheus_port: int = Field(
        default=9090,
        description="Prometheus metrics port",
        ge=1,
        le=65535
    )

    # MCP Configuration
    mcp_server_name: str = Field(
        default="fin-hub",
        description="MCP server name"
    )
    mcp_protocol_version: str = Field(
        default="2024-11-05",
        description="MCP protocol version"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @validator("environment", pre=True)
    def validate_environment(cls, v):
        if isinstance(v, str):
            return Environment(v.lower())
        return v

    @validator("log_level", pre=True)
    def validate_log_level(cls, v):
        if isinstance(v, str):
            return LogLevel(v.upper())
        return v

    @validator("log_format", pre=True)
    def validate_log_format(cls, v):
        if isinstance(v, str):
            return LogFormat(v.lower())
        return v

    @validator("debug", pre=True)
    def validate_debug(cls, v, values):
        # Auto-enable debug in development
        if values.get("environment") == Environment.DEVELOPMENT and v is None:
            return True
        return bool(v) if v is not None else False

    @validator("log_file_path", pre=True)
    def validate_log_file_path(cls, v):
        if v:
            # Expand environment variables and user home
            path = Path(os.path.expandvars(os.path.expanduser(v)))
            return str(path.absolute())
        return v

    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration dictionary"""
        if not self.database_url:
            return {}

        return {
            "url": self.database_url,
            "pool_size": self.db_pool_size,
            "pool_overflow": self.db_pool_overflow,
            "echo": self.debug,
            "future": True
        }

    def get_redis_config(self) -> Dict[str, Any]:
        """Get Redis configuration dictionary"""
        return {
            "url": self.redis_url,
            "pool_size": self.redis_pool_size,
            "decode_responses": True,
            "retry_on_timeout": True
        }

    def get_consul_config(self) -> Dict[str, Any]:
        """Get Consul configuration dictionary"""
        config = {
            "host": self.consul_host,
            "port": self.consul_port,
            "datacenter": self.consul_datacenter
        }
        if self.consul_token:
            config["token"] = self.consul_token
        return config

    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration dictionary"""
        return {
            "service_name": self.service_name,
            "log_level": self.log_level.value,
            "log_format": self.log_format.value,
            "log_file_path": self.log_file_path,
            "enable_console": True
        }

    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment == Environment.PRODUCTION

    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment == Environment.DEVELOPMENT

    def is_testing(self) -> bool:
        """Check if running in testing"""
        return self.environment == Environment.TESTING


class HubServerConfig(BaseConfig):
    """Configuration specific to Hub Server"""

    service_name: str = Field(default="hub-server")

    # Hub-specific settings
    hub_url: str = Field(
        default="http://localhost:8000",
        description="Hub server URL for service registration"
    )

    # Tool registry settings
    tool_registry_enabled: bool = Field(
        default=True,
        description="Enable tool registry functionality"
    )
    auto_discovery_enabled: bool = Field(
        default=True,
        description="Enable automatic service discovery"
    )
    health_check_interval: int = Field(
        default=30,
        description="Health check interval in seconds",
        ge=5
    )


class SpokeServiceConfig(BaseConfig):
    """Configuration specific to Spoke services"""

    # Hub connection
    hub_url: str = Field(
        default="http://hub-server:8000",
        description="Hub server URL for registration"
    )
    auto_register: bool = Field(
        default=True,
        description="Automatically register with hub on startup"
    )
    registration_retry_attempts: int = Field(
        default=3,
        description="Number of registration retry attempts",
        ge=1
    )
    registration_retry_delay: int = Field(
        default=5,
        description="Delay between registration retries in seconds",
        ge=1
    )

    # Service-specific settings
    service_tags: List[str] = Field(
        default_factory=list,
        description="Service tags for discovery"
    )
    service_meta: Dict[str, str] = Field(
        default_factory=dict,
        description="Service metadata"
    )

    # External API settings (for market-spoke)
    external_api_timeout: int = Field(
        default=30,
        description="External API request timeout in seconds",
        ge=1
    )
    external_api_retries: int = Field(
        default=3,
        description="External API retry attempts",
        ge=0
    )

    @validator("service_tags", pre=True)
    def validate_service_tags(cls, v):
        if isinstance(v, str):
            return [tag.strip() for tag in v.split(",") if tag.strip()]
        return v or []