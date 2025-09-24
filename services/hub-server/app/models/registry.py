"""
Database models for service registry
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from sqlalchemy import (
    String, Integer, DateTime, Text, Boolean, JSON,
    Index, UniqueConstraint, ForeignKey
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from ..core.database import Base


class Service(Base):
    """Service registration model"""
    __tablename__ = "services"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Service identification
    service_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique service identifier"
    )

    service_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Service name for grouping"
    )

    # Network information
    address: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Service IP address or hostname"
    )

    port: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Service port number"
    )

    # Service metadata
    version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="1.0.0",
        comment="Service version"
    )

    tags: Mapped[List[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        comment="Service tags for filtering"
    )

    meta: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        comment="Service metadata"
    )

    # Health and status
    health_check_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Health check endpoint URL"
    )

    health_check_interval: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=30,
        comment="Health check interval in seconds"
    )

    is_healthy: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Current health status"
    )

    consecutive_failures: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Consecutive health check failures"
    )

    last_health_check: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last health check timestamp"
    )

    # Load balancing
    weight: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=100,
        comment="Load balancing weight"
    )

    current_load: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Current load (active connections/requests)"
    )

    # Registration tracking
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment="Service registration timestamp"
    )

    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment="Last activity timestamp"
    )

    ttl_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=300,
        comment="Time to live in seconds"
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether service is active"
    )

    # Relationships
    tools: Mapped[List["Tool"]] = relationship(
        "Tool",
        back_populates="service",
        cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("ix_services_name_active", "service_name", "is_active"),
        Index("ix_services_health", "is_healthy", "last_health_check"),
        Index("ix_services_ttl", "last_seen", "ttl_seconds"),
        UniqueConstraint("service_id", name="uq_service_id"),
    )

    def __repr__(self) -> str:
        return f"<Service(service_id='{self.service_id}', name='{self.service_name}')>"

    @property
    def is_expired(self) -> bool:
        """Check if service registration has expired"""
        if not self.last_seen:
            return True

        expired_time = self.last_seen.replace(tzinfo=timezone.utc) + \
                      datetime.timedelta(seconds=self.ttl_seconds)
        return datetime.now(timezone.utc) > expired_time

    @property
    def service_url(self) -> str:
        """Get service base URL"""
        return f"http://{self.address}:{self.port}"

    def update_last_seen(self):
        """Update last seen timestamp"""
        self.last_seen = datetime.now(timezone.utc)

    def update_health_status(self, is_healthy: bool):
        """Update health status and failure count"""
        self.is_healthy = is_healthy
        self.last_health_check = datetime.now(timezone.utc)

        if is_healthy:
            self.consecutive_failures = 0
        else:
            self.consecutive_failures += 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "service_id": self.service_id,
            "service_name": self.service_name,
            "address": self.address,
            "port": self.port,
            "version": self.version,
            "tags": self.tags,
            "meta": self.meta,
            "health_check_url": self.health_check_url,
            "is_healthy": self.is_healthy,
            "consecutive_failures": self.consecutive_failures,
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "weight": self.weight,
            "current_load": self.current_load,
            "registered_at": self.registered_at.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "ttl_seconds": self.ttl_seconds,
            "is_active": self.is_active,
            "service_url": self.service_url,
            "is_expired": self.is_expired
        }