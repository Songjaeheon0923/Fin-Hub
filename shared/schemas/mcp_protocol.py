"""
MCP (Model Context Protocol) Standard Schemas
MCP Protocol Version: 2024-11-05
"""

from typing import Any, Dict, List, Optional, Union, Literal
from pydantic import BaseModel, Field
from enum import Enum


class MCPVersion(str, Enum):
    """MCP Protocol Version"""
    V1 = "2024-11-05"


class ToolCapability(str, Enum):
    """Tool capabilities supported by the server"""
    TOOLS = "tools"
    RESOURCES = "resources"
    PROMPTS = "prompts"
    LOGGING = "logging"


class MCPErrorCode(str, Enum):
    """Standard MCP error codes"""
    PARSE_ERROR = "PARSE_ERROR"
    INVALID_REQUEST = "INVALID_REQUEST"
    METHOD_NOT_FOUND = "METHOD_NOT_FOUND"
    INVALID_PARAMS = "INVALID_PARAMS"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVER_ERROR = "SERVER_ERROR"


# Base MCP Message Types
class MCPMessage(BaseModel):
    """Base MCP message structure"""
    jsonrpc: str = Field(default="2.0", description="JSON-RPC version")


class MCPRequest(MCPMessage):
    """MCP Request message"""
    id: Union[str, int, None] = Field(description="Request ID")
    method: str = Field(description="Method name")
    params: Optional[Dict[str, Any]] = Field(default=None, description="Method parameters")


class MCPResponse(MCPMessage):
    """MCP Response message"""
    id: Union[str, int, None] = Field(description="Request ID")
    result: Optional[Any] = Field(default=None, description="Success result")
    error: Optional[Dict[str, Any]] = Field(default=None, description="Error details")


class MCPNotification(MCPMessage):
    """MCP Notification message (no response expected)"""
    method: str = Field(description="Notification method")
    params: Optional[Dict[str, Any]] = Field(default=None, description="Notification parameters")


# Server Capabilities
class ServerCapabilities(BaseModel):
    """Server capabilities declaration"""
    tools: Optional[Dict[str, Any]] = Field(default=None, description="Tool capabilities")
    resources: Optional[Dict[str, Any]] = Field(default=None, description="Resource capabilities")
    prompts: Optional[Dict[str, Any]] = Field(default=None, description="Prompt capabilities")
    logging: Optional[Dict[str, Any]] = Field(default=None, description="Logging capabilities")


class ServerInfo(BaseModel):
    """Server information"""
    name: str = Field(description="Server name")
    version: str = Field(description="Server version")
    protocol_version: str = Field(default=MCPVersion.V1, description="MCP protocol version")


class InitializeRequest(BaseModel):
    """Initialize request parameters"""
    protocol_version: str = Field(description="Client MCP protocol version")
    capabilities: Dict[str, Any] = Field(description="Client capabilities")
    client_info: Dict[str, str] = Field(description="Client information")


class InitializeResponse(BaseModel):
    """Initialize response"""
    protocol_version: str = Field(description="Server MCP protocol version")
    capabilities: ServerCapabilities = Field(description="Server capabilities")
    server_info: ServerInfo = Field(description="Server information")


# Tool Schemas
class ToolInputSchema(BaseModel):
    """Tool input parameter schema"""
    type: str = Field(default="object", description="Schema type")
    properties: Dict[str, Any] = Field(description="Parameter properties")
    required: Optional[List[str]] = Field(default=None, description="Required parameters")


class Tool(BaseModel):
    """Tool definition"""
    name: str = Field(description="Tool name (e.g., 'market.get_price')")
    description: str = Field(description="Tool description")
    input_schema: ToolInputSchema = Field(description="Input parameter schema")


class ToolsListResponse(BaseModel):
    """Tools list response"""
    tools: List[Tool] = Field(description="Available tools")


class ToolCallRequest(BaseModel):
    """Tool execution request"""
    name: str = Field(description="Tool name to execute")
    arguments: Dict[str, Any] = Field(description="Tool arguments")


class ToolResult(BaseModel):
    """Tool execution result"""
    content: List[Dict[str, Any]] = Field(description="Tool result content")
    is_error: Optional[bool] = Field(default=False, description="Whether result is an error")


class ToolCallResponse(BaseModel):
    """Tool execution response"""
    result: ToolResult = Field(description="Tool execution result")


# Resource Schemas (for future use)
class Resource(BaseModel):
    """Resource definition"""
    uri: str = Field(description="Resource URI")
    name: str = Field(description="Resource name")
    description: Optional[str] = Field(default=None, description="Resource description")
    mime_type: Optional[str] = Field(default=None, description="MIME type")


class ResourcesListResponse(BaseModel):
    """Resources list response"""
    resources: List[Resource] = Field(description="Available resources")


# Error Schemas
class MCPError(BaseModel):
    """MCP Error details"""
    code: MCPErrorCode = Field(description="Error code")
    message: str = Field(description="Error message")
    data: Optional[Any] = Field(default=None, description="Additional error data")


# Health Check Schema
class HealthStatus(BaseModel):
    """Service health status"""
    status: Literal["healthy", "unhealthy", "degraded"] = Field(description="Health status")
    timestamp: str = Field(description="Check timestamp")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional details")


# Service Registry Schemas
class ServiceRegistration(BaseModel):
    """Service registration info for Consul"""
    service_id: str = Field(description="Unique service ID")
    service_name: str = Field(description="Service name")
    address: str = Field(description="Service address")
    port: int = Field(description="Service port")
    tags: List[str] = Field(default_factory=list, description="Service tags")
    meta: Dict[str, str] = Field(default_factory=dict, description="Service metadata")
    health_check: Optional[Dict[str, Any]] = Field(default=None, description="Health check config")


class ToolMetadata(BaseModel):
    """Tool metadata for registry"""
    tool_id: str = Field(description="Tool identifier")
    service_id: str = Field(description="Parent service ID")
    name: str = Field(description="Tool name")
    description: str = Field(description="Tool description")
    version: str = Field(description="Tool version")
    schema: Tool = Field(description="Tool schema")
    created_at: str = Field(description="Creation timestamp")
    updated_at: str = Field(description="Last update timestamp")


# Fin-Hub Specific Schemas
class FinHubToolCategories(str, Enum):
    """Fin-Hub tool categories"""
    MARKET = "market"
    RISK = "risk"
    PORTFOLIO = "portfolio"


class MarketToolResult(BaseModel):
    """Market analysis tool result"""
    symbol: str = Field(description="Stock symbol")
    data: Dict[str, Any] = Field(description="Market data")
    timestamp: str = Field(description="Data timestamp")
    source: str = Field(description="Data source")


class RiskToolResult(BaseModel):
    """Risk analysis tool result"""
    risk_score: float = Field(description="Risk score (0-1)")
    risk_level: Literal["low", "medium", "high"] = Field(description="Risk level")
    details: Dict[str, Any] = Field(description="Risk analysis details")
    recommendations: List[str] = Field(description="Risk mitigation recommendations")


class PortfolioToolResult(BaseModel):
    """Portfolio tool result"""
    allocation: Dict[str, float] = Field(description="Asset allocation percentages")
    expected_return: Optional[float] = Field(description="Expected return")
    risk_metrics: Dict[str, float] = Field(description="Risk metrics")
    rebalancing_needed: bool = Field(description="Whether rebalancing is needed")