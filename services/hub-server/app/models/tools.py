"""
Database models for tool registry
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from sqlalchemy import (
    String, Integer, DateTime, Text, Boolean, JSON,
    Index, ForeignKey
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from ..core.database import Base


class Tool(Base):
    """Tool registration model"""
    __tablename__ = "tools"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Tool identification
    tool_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Tool identifier (e.g., 'market.get_price')"
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Human-readable tool name"
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Tool description"
    )

    # Tool metadata
    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Tool category (market, risk, portfolio)"
    )

    version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="1.0.0",
        comment="Tool version"
    )

    tags: Mapped[List[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        comment="Tool tags for filtering"
    )

    # MCP Schema
    input_schema: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        comment="Tool input schema (MCP format)"
    )

    output_schema: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Tool output schema (optional)"
    )

    # Execution settings
    timeout_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=300,
        comment="Tool execution timeout in seconds"
    )

    retry_attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=3,
        comment="Number of retry attempts on failure"
    )

    # Performance metrics
    total_executions: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Total number of executions"
    )

    successful_executions: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of successful executions"
    )

    average_duration_ms: Mapped[Optional[float]] = mapped_column(
        nullable=True,
        comment="Average execution duration in milliseconds"
    )

    last_executed: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last execution timestamp"
    )

    # Status
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether tool is enabled for execution"
    )

    # Registration tracking
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment="Tool registration timestamp"
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="Last update timestamp"
    )

    # Foreign key to service
    service_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("services.id", ondelete="CASCADE"),
        nullable=False,
        comment="Parent service ID"
    )

    # Relationships
    service: Mapped["Service"] = relationship(
        "Service",
        back_populates="tools"
    )

    # Indexes
    __table_args__ = (
        Index("ix_tools_category_enabled", "category", "is_enabled"),
        Index("ix_tools_service_enabled", "service_id", "is_enabled"),
        Index("ix_tools_execution_stats", "total_executions", "last_executed"),
        Index("ix_tools_unique_per_service", "service_id", "tool_id", unique=True),
    )

    def __repr__(self) -> str:
        return f"<Tool(tool_id='{self.tool_id}', category='{self.category}')>"

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_executions == 0:
            return 0.0
        return (self.successful_executions / self.total_executions) * 100

    def update_execution_stats(self, success: bool, duration_ms: float):
        """Update execution statistics"""
        self.total_executions += 1
        if success:
            self.successful_executions += 1

        # Update average duration
        if self.average_duration_ms is None:
            self.average_duration_ms = duration_ms
        else:
            # Exponential moving average
            alpha = 0.1  # Smoothing factor
            self.average_duration_ms = (
                alpha * duration_ms +
                (1 - alpha) * self.average_duration_ms
            )

        self.last_executed = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "tool_id": self.tool_id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "version": self.version,
            "tags": self.tags,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "timeout_seconds": self.timeout_seconds,
            "retry_attempts": self.retry_attempts,
            "total_executions": self.total_executions,
            "successful_executions": self.successful_executions,
            "success_rate": self.success_rate,
            "average_duration_ms": self.average_duration_ms,
            "last_executed": self.last_executed.isoformat() if self.last_executed else None,
            "is_enabled": self.is_enabled,
            "registered_at": self.registered_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "service_id": str(self.service_id)
        }

    def to_mcp_schema(self) -> Dict[str, Any]:
        """Convert to MCP tool schema format"""
        return {
            "name": self.tool_id,
            "description": self.description,
            "input_schema": self.input_schema
        }


class ToolExecution(Base):
    """Tool execution history and results"""
    __tablename__ = "tool_executions"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Execution identification
    execution_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="Unique execution identifier"
    )

    correlation_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="Request correlation ID"
    )

    # Tool reference
    tool_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Tool that was executed"
    )

    service_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Service that executed the tool"
    )

    # Execution details
    input_data: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        comment="Tool input parameters"
    )

    output_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Tool output result"
    )

    error_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Error information if execution failed"
    )

    # Status and timing
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="running",
        index=True,
        comment="Execution status (running, completed, failed, timeout)"
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment="Execution start timestamp"
    )

    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Execution completion timestamp"
    )

    duration_ms: Mapped[Optional[float]] = mapped_column(
        nullable=True,
        comment="Execution duration in milliseconds"
    )

    # Metadata
    user_agent: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Client user agent"
    )

    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
        comment="Client IP address"
    )

    # Indexes
    __table_args__ = (
        Index("ix_executions_tool_status", "tool_id", "status"),
        Index("ix_executions_service_status", "service_id", "status"),
        Index("ix_executions_started_at", "started_at"),
        Index("ix_executions_correlation", "correlation_id"),
    )

    def __repr__(self) -> str:
        return f"<ToolExecution(execution_id='{self.execution_id}', tool_id='{self.tool_id}')>"

    def complete_execution(self, output_data: Dict[str, Any], status: str = "completed"):
        """Mark execution as completed"""
        self.output_data = output_data
        self.status = status
        self.completed_at = datetime.now(timezone.utc)

        if self.started_at:
            self.duration_ms = (
                self.completed_at - self.started_at
            ).total_seconds() * 1000

    def fail_execution(self, error_data: Dict[str, Any], status: str = "failed"):
        """Mark execution as failed"""
        self.error_data = error_data
        self.status = status
        self.completed_at = datetime.now(timezone.utc)

        if self.started_at:
            self.duration_ms = (
                self.completed_at - self.started_at
            ).total_seconds() * 1000

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "execution_id": self.execution_id,
            "correlation_id": self.correlation_id,
            "tool_id": self.tool_id,
            "service_id": self.service_id,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "error_data": self.error_data,
            "status": self.status,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": self.duration_ms,
            "user_agent": self.user_agent,
            "ip_address": self.ip_address
        }