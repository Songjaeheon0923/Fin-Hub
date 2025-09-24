"""
Health Check Utilities for Fin-Hub Services
Provides standardized health checking across all services
"""

import asyncio
import time
from typing import Dict, Any, Optional, List, Callable, Awaitable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import aiohttp
import redis.asyncio as aioredis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from ..schemas.mcp_protocol import HealthStatus


class CheckStatus(str, Enum):
    """Health check status values"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


@dataclass
class CheckResult:
    """Individual health check result"""
    name: str
    status: CheckStatus
    message: str
    duration_ms: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "duration_ms": round(self.duration_ms, 2),
            "timestamp": self.timestamp.isoformat(),
            "details": self.details or {}
        }


@dataclass
class HealthCheckResult:
    """Overall health check result"""
    status: CheckStatus
    timestamp: datetime
    checks: List[CheckResult] = field(default_factory=list)
    service_info: Optional[Dict[str, Any]] = None

    @property
    def is_healthy(self) -> bool:
        """Check if overall status is healthy"""
        return self.status == CheckStatus.HEALTHY

    def add_check(self, check: CheckResult):
        """Add individual check result"""
        self.checks.append(check)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
            "checks": [check.to_dict() for check in self.checks],
            "service_info": self.service_info or {}
        }


class HealthChecker:
    """Centralized health checker for services"""

    def __init__(self, service_name: str, service_version: str = "1.0.0"):
        self.service_name = service_name
        self.service_version = service_version
        self.checks: List[Callable[[], Awaitable[CheckResult]]] = []

    async def _time_check(self, check_func: Callable[[], Awaitable[CheckResult]]) -> CheckResult:
        """Time a health check execution"""
        start_time = time.time()
        try:
            result = await check_func()
            duration_ms = (time.time() - start_time) * 1000
            result.duration_ms = duration_ms
            return result
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return CheckResult(
                name="unknown",
                status=CheckStatus.UNHEALTHY,
                message=f"Check failed: {str(e)}",
                duration_ms=duration_ms,
                details={"exception": str(e)}
            )

    def add_check(self, check_func: Callable[[], Awaitable[CheckResult]]):
        """Add a health check function"""
        self.checks.append(check_func)

    async def check_all(self) -> HealthCheckResult:
        """Execute all health checks"""
        timestamp = datetime.utcnow()
        checks = []

        # Run all checks concurrently
        if self.checks:
            check_tasks = [self._time_check(check) for check in self.checks]
            checks = await asyncio.gather(*check_tasks, return_exceptions=True)

        # Handle any exceptions from checks
        valid_checks = []
        for check in checks:
            if isinstance(check, Exception):
                valid_checks.append(CheckResult(
                    name="exception",
                    status=CheckStatus.UNHEALTHY,
                    message=f"Check exception: {str(check)}",
                    duration_ms=0.0
                ))
            else:
                valid_checks.append(check)

        # Determine overall status
        overall_status = self._determine_overall_status(valid_checks)

        return HealthCheckResult(
            status=overall_status,
            timestamp=timestamp,
            checks=valid_checks,
            service_info={
                "name": self.service_name,
                "version": self.service_version,
                "uptime": self._get_uptime()
            }
        )

    def _determine_overall_status(self, checks: List[CheckResult]) -> CheckStatus:
        """Determine overall status from individual checks"""
        if not checks:
            return CheckStatus.HEALTHY

        unhealthy_count = sum(1 for check in checks if check.status == CheckStatus.UNHEALTHY)
        degraded_count = sum(1 for check in checks if check.status == CheckStatus.DEGRADED)

        if unhealthy_count > 0:
            return CheckStatus.UNHEALTHY
        elif degraded_count > 0:
            return CheckStatus.DEGRADED
        else:
            return CheckStatus.HEALTHY

    def _get_uptime(self) -> str:
        """Get service uptime (placeholder - would need actual start time tracking)"""
        # This would need to be implemented with actual service start time
        return "unknown"


# Pre-built health check functions
class StandardHealthChecks:
    """Standard health check implementations"""

    @staticmethod
    def create_database_check(engine: AsyncEngine, timeout: float = 5.0) -> Callable[[], Awaitable[CheckResult]]:
        """Create database connectivity health check"""

        async def check_database() -> CheckResult:
            try:
                # Test basic connectivity with timeout
                async with asyncio.timeout(timeout):
                    async with engine.begin() as conn:
                        result = await conn.execute(text("SELECT 1"))
                        await result.fetchone()

                return CheckResult(
                    name="database",
                    status=CheckStatus.HEALTHY,
                    message="Database connection successful",
                    duration_ms=0.0  # Will be set by timer
                )

            except asyncio.TimeoutError:
                return CheckResult(
                    name="database",
                    status=CheckStatus.UNHEALTHY,
                    message=f"Database connection timeout after {timeout}s",
                    duration_ms=0.0
                )
            except Exception as e:
                return CheckResult(
                    name="database",
                    status=CheckStatus.UNHEALTHY,
                    message=f"Database connection failed: {str(e)}",
                    duration_ms=0.0,
                    details={"exception_type": type(e).__name__}
                )

        return check_database

    @staticmethod
    def create_redis_check(redis_url: str, timeout: float = 5.0) -> Callable[[], Awaitable[CheckResult]]:
        """Create Redis connectivity health check"""

        async def check_redis() -> CheckResult:
            redis_client = None
            try:
                async with asyncio.timeout(timeout):
                    redis_client = aioredis.from_url(redis_url)
                    await redis_client.ping()

                return CheckResult(
                    name="redis",
                    status=CheckStatus.HEALTHY,
                    message="Redis connection successful",
                    duration_ms=0.0
                )

            except asyncio.TimeoutError:
                return CheckResult(
                    name="redis",
                    status=CheckStatus.UNHEALTHY,
                    message=f"Redis connection timeout after {timeout}s",
                    duration_ms=0.0
                )
            except Exception as e:
                return CheckResult(
                    name="redis",
                    status=CheckStatus.UNHEALTHY,
                    message=f"Redis connection failed: {str(e)}",
                    duration_ms=0.0,
                    details={"exception_type": type(e).__name__}
                )
            finally:
                if redis_client:
                    await redis_client.close()

        return check_redis

    @staticmethod
    def create_consul_check(consul_host: str, consul_port: int, timeout: float = 5.0) -> Callable[[], Awaitable[CheckResult]]:
        """Create Consul connectivity health check"""

        async def check_consul() -> CheckResult:
            try:
                async with asyncio.timeout(timeout):
                    async with aiohttp.ClientSession() as session:
                        url = f"http://{consul_host}:{consul_port}/v1/status/leader"
                        async with session.get(url) as response:
                            if response.status == 200:
                                leader = await response.text()
                                return CheckResult(
                                    name="consul",
                                    status=CheckStatus.HEALTHY,
                                    message="Consul connection successful",
                                    duration_ms=0.0,
                                    details={"leader": leader.strip('"')}
                                )
                            else:
                                return CheckResult(
                                    name="consul",
                                    status=CheckStatus.DEGRADED,
                                    message=f"Consul responded with status {response.status}",
                                    duration_ms=0.0
                                )

            except asyncio.TimeoutError:
                return CheckResult(
                    name="consul",
                    status=CheckStatus.UNHEALTHY,
                    message=f"Consul connection timeout after {timeout}s",
                    duration_ms=0.0
                )
            except Exception as e:
                return CheckResult(
                    name="consul",
                    status=CheckStatus.UNHEALTHY,
                    message=f"Consul connection failed: {str(e)}",
                    duration_ms=0.0,
                    details={"exception_type": type(e).__name__}
                )

        return check_consul

    @staticmethod
    def create_external_service_check(
        name: str,
        url: str,
        timeout: float = 10.0,
        expected_status: int = 200
    ) -> Callable[[], Awaitable[CheckResult]]:
        """Create external service health check"""

        async def check_external_service() -> CheckResult:
            try:
                async with asyncio.timeout(timeout):
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url) as response:
                            if response.status == expected_status:
                                return CheckResult(
                                    name=name,
                                    status=CheckStatus.HEALTHY,
                                    message=f"{name} service is accessible",
                                    duration_ms=0.0,
                                    details={"status_code": response.status}
                                )
                            else:
                                return CheckResult(
                                    name=name,
                                    status=CheckStatus.DEGRADED,
                                    message=f"{name} returned status {response.status}",
                                    duration_ms=0.0,
                                    details={"status_code": response.status}
                                )

            except asyncio.TimeoutError:
                return CheckResult(
                    name=name,
                    status=CheckStatus.UNHEALTHY,
                    message=f"{name} timeout after {timeout}s",
                    duration_ms=0.0
                )
            except Exception as e:
                return CheckResult(
                    name=name,
                    status=CheckStatus.UNHEALTHY,
                    message=f"{name} check failed: {str(e)}",
                    duration_ms=0.0,
                    details={"exception_type": type(e).__name__}
                )

        return check_external_service

    @staticmethod
    def create_memory_usage_check(threshold_percent: float = 90.0) -> Callable[[], Awaitable[CheckResult]]:
        """Create memory usage health check"""

        async def check_memory_usage() -> CheckResult:
            try:
                import psutil
                memory = psutil.virtual_memory()
                used_percent = memory.percent

                if used_percent > threshold_percent:
                    status = CheckStatus.UNHEALTHY
                    message = f"High memory usage: {used_percent:.1f}%"
                elif used_percent > threshold_percent * 0.8:  # 80% of threshold
                    status = CheckStatus.DEGRADED
                    message = f"Elevated memory usage: {used_percent:.1f}%"
                else:
                    status = CheckStatus.HEALTHY
                    message = f"Memory usage normal: {used_percent:.1f}%"

                return CheckResult(
                    name="memory_usage",
                    status=status,
                    message=message,
                    duration_ms=0.0,
                    details={
                        "used_percent": used_percent,
                        "available_mb": memory.available // 1024 // 1024,
                        "total_mb": memory.total // 1024 // 1024
                    }
                )

            except ImportError:
                return CheckResult(
                    name="memory_usage",
                    status=CheckStatus.DEGRADED,
                    message="psutil not available for memory monitoring",
                    duration_ms=0.0
                )
            except Exception as e:
                return CheckResult(
                    name="memory_usage",
                    status=CheckStatus.UNHEALTHY,
                    message=f"Memory check failed: {str(e)}",
                    duration_ms=0.0,
                    details={"exception_type": type(e).__name__}
                )

        return check_memory_usage


# FastAPI integration
def create_health_endpoint(health_checker: HealthChecker):
    """Create FastAPI health endpoint"""

    async def health_endpoint():
        """Health check endpoint"""
        result = await health_checker.check_all()

        status_code = 200
        if result.status == CheckStatus.DEGRADED:
            status_code = 200  # Still operational but degraded
        elif result.status == CheckStatus.UNHEALTHY:
            status_code = 503  # Service unavailable

        from fastapi import Response
        return Response(
            content=result.to_dict(),
            media_type="application/json",
            status_code=status_code
        )

    return health_endpoint