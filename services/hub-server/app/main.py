"""
Fin-Hub Server - Main FastAPI Application
MCP-compliant AI agent hub for financial tools integration
"""

import asyncio
import logging
import uuid
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from shared.schemas.mcp_protocol import (
    ServiceRegistration, MCPRequest, MCPResponse, MCPError, MCPErrorCode
)
from shared.utils.logging import setup_logging, LoggerMixin, get_correlation_id, set_correlation_id
from shared.utils.health_check import HealthChecker

from .core.config import get_config
from .core.database import init_database, close_database
from .services.registry_service import RegistryService
from .services.execution_service import ExecutionService
from .services.mcp_server import MCPServer


# Global services
registry_service: Optional[RegistryService] = None
execution_service: Optional[ExecutionService] = None
mcp_server: Optional[MCPServer] = None
health_checker: Optional[HealthChecker] = None

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global registry_service, execution_service, mcp_server, health_checker

    config = get_config()

    # Setup logging
    setup_logging(
        log_level=config.log_level,
        service_name="hub-server"
    )

    logger.info("Starting Fin-Hub Server...")

    try:
        # Initialize database
        await init_database()

        # Initialize services
        registry_service = RegistryService()
        await registry_service.start()

        execution_service = ExecutionService(registry_service)

        mcp_server = MCPServer(registry_service, execution_service)
        await mcp_server.start()

        # Initialize health checker
        health_checker = HealthChecker(config)

        logger.info("Fin-Hub Server started successfully")

        yield

    except Exception as e:
        logger.error(f"Failed to start Fin-Hub Server: {e}", exc_info=e)
        raise

    finally:
        # Cleanup
        logger.info("Shutting down Fin-Hub Server...")

        if mcp_server:
            await mcp_server.stop()

        if registry_service:
            await registry_service.stop()

        await close_database()

        logger.info("Fin-Hub Server stopped")


# Create FastAPI app
app = FastAPI(
    title="Fin-Hub Server",
    description="MCP-compliant AI agent hub for financial tools integration",
    version="1.0.0",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    """Add correlation ID to requests"""
    correlation_id = request.headers.get("x-correlation-id") or str(uuid.uuid4())
    set_correlation_id(correlation_id)

    response = await call_next(request)
    response.headers["x-correlation-id"] = correlation_id

    return response


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Log requests and responses"""
    start_time = asyncio.get_event_loop().time()

    logger.info(
        f"Request: {request.method} {request.url.path}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "correlation_id": get_correlation_id()
        }
    )

    response = await call_next(request)

    duration = asyncio.get_event_loop().time() - start_time

    logger.info(
        f"Response: {response.status_code} in {duration:.3f}s",
        extra={
            "status_code": response.status_code,
            "duration_ms": duration * 1000,
            "correlation_id": get_correlation_id()
        }
    )

    return response


def get_registry() -> RegistryService:
    """Dependency to get registry service"""
    if not registry_service:
        raise HTTPException(status_code=503, detail="Registry service not available")
    return registry_service


def get_execution() -> ExecutionService:
    """Dependency to get execution service"""
    if not execution_service:
        raise HTTPException(status_code=503, detail="Execution service not available")
    return execution_service


def get_mcp() -> MCPServer:
    """Dependency to get MCP server"""
    if not mcp_server:
        raise HTTPException(status_code=503, detail="MCP server not available")
    return mcp_server


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    if not health_checker:
        return {"status": "starting"}

    health_status = await health_checker.check_all()

    if health_status["healthy"]:
        return JSONResponse(
            status_code=200,
            content=health_status
        )
    else:
        return JSONResponse(
            status_code=503,
            content=health_status
        )


# Service registration endpoints
@app.post("/api/v1/services/register")
async def register_service(
    registration_data: Dict[str, Any],
    registry: RegistryService = Depends(get_registry)
):
    """Register a new service"""
    try:
        # Parse registration data
        registration = ServiceRegistration(**registration_data)
        tools = registration_data.get("tools", [])

        success = await registry.register_service(registration, tools)

        if success:
            return {
                "success": True,
                "message": f"Service {registration.service_id} registered successfully",
                "service_id": registration.service_id
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to register service"
            )

    except Exception as e:
        logger.error(f"Service registration failed: {e}", exc_info=e)
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/services/{service_id}/deregister")
async def deregister_service(
    service_id: str,
    registry: RegistryService = Depends(get_registry)
):
    """Deregister a service"""
    try:
        success = await registry.deregister_service(service_id)

        if success:
            return {
                "success": True,
                "message": f"Service {service_id} deregistered successfully"
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Service not found"
            )

    except Exception as e:
        logger.error(f"Service deregistration failed: {e}", exc_info=e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/services")
async def discover_services(
    service_name: Optional[str] = None,
    tags: Optional[str] = None,
    healthy_only: bool = True,
    registry: RegistryService = Depends(get_registry)
):
    """Discover services"""
    try:
        tag_list = tags.split(",") if tags else None

        services = await registry.discover_services(
            service_name=service_name,
            tags=tag_list,
            healthy_only=healthy_only
        )

        return {
            "services": [
                {
                    **service.service.to_dict(),
                    "tools": [tool.to_dict() for tool in service.tools]
                }
                for service in services
            ]
        }

    except Exception as e:
        logger.error(f"Service discovery failed: {e}", exc_info=e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/services/{service_id}")
async def get_service(
    service_id: str,
    registry: RegistryService = Depends(get_registry)
):
    """Get specific service details"""
    try:
        service = await registry.get_service(service_id)

        if service:
            return {
                **service.service.to_dict(),
                "tools": [tool.to_dict() for tool in service.tools]
            }
        else:
            raise HTTPException(status_code=404, detail="Service not found")

    except Exception as e:
        logger.error(f"Failed to get service {service_id}: {e}", exc_info=e)
        raise HTTPException(status_code=500, detail=str(e))


# Tool endpoints
@app.get("/api/v1/tools")
async def list_tools(registry: RegistryService = Depends(get_registry)):
    """List all available tools"""
    try:
        tools = await registry.get_all_tools()

        return {
            "tools": [tool.to_dict() for tool in tools]
        }

    except Exception as e:
        logger.error(f"Failed to list tools: {e}", exc_info=e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/tools/{tool_id}")
async def get_tool(
    tool_id: str,
    registry: RegistryService = Depends(get_registry)
):
    """Get specific tool details"""
    try:
        tool = await registry.get_tool(tool_id)

        if tool:
            return tool.to_dict()
        else:
            raise HTTPException(status_code=404, detail="Tool not found")

    except Exception as e:
        logger.error(f"Failed to get tool {tool_id}: {e}", exc_info=e)
        raise HTTPException(status_code=500, detail=str(e))


# Tool execution endpoints
@app.post("/api/v1/tools/{tool_id}/execute")
async def execute_tool(
    tool_id: str,
    execution_request: Dict[str, Any],
    execution: ExecutionService = Depends(get_execution)
):
    """Execute a tool"""
    try:
        arguments = execution_request.get("arguments", {})
        timeout_seconds = execution_request.get("timeout_seconds")

        result = await execution.execute_tool(
            tool_name=tool_id,
            arguments=arguments,
            correlation_id=get_correlation_id(),
            timeout_seconds=timeout_seconds
        )

        return result

    except Exception as e:
        logger.error(f"Tool execution failed: {e}", exc_info=e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/executions/{execution_id}")
async def get_execution_status(
    execution_id: str,
    execution: ExecutionService = Depends(get_execution)
):
    """Get execution status"""
    try:
        status = await execution.get_execution_status(execution_id)

        if status:
            return status
        else:
            raise HTTPException(status_code=404, detail="Execution not found")

    except Exception as e:
        logger.error(f"Failed to get execution status: {e}", exc_info=e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/executions/{execution_id}/cancel")
async def cancel_execution(
    execution_id: str,
    execution: ExecutionService = Depends(get_execution)
):
    """Cancel execution"""
    try:
        success = await execution.cancel_execution(execution_id)

        return {
            "success": success,
            "message": f"Execution {'cancelled' if success else 'not found or already completed'}"
        }

    except Exception as e:
        logger.error(f"Failed to cancel execution: {e}", exc_info=e)
        raise HTTPException(status_code=500, detail=str(e))


# MCP Protocol endpoint
@app.post("/mcp")
async def mcp_endpoint(
    request: Request,
    mcp: MCPServer = Depends(get_mcp)
):
    """MCP protocol endpoint"""
    try:
        # Read request body
        body = await request.body()
        message = body.decode('utf-8')

        # Handle MCP message
        response = await mcp.handle_message(message)

        if response:
            return JSONResponse(
                status_code=200,
                content=response,
                media_type="application/json"
            )
        else:
            # Notification - no response
            return Response(status_code=204)

    except Exception as e:
        logger.error(f"MCP endpoint error: {e}", exc_info=e)

        # Return MCP error response
        error_response = {
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": MCPErrorCode.INTERNAL_ERROR.value,
                "message": f"MCP handler error: {str(e)}"
            }
        }

        return JSONResponse(
            status_code=200,  # MCP errors are still HTTP 200
            content=error_response
        )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with server information"""
    config = get_config()

    return {
        "name": "Fin-Hub Server",
        "version": "1.0.0",
        "description": "MCP-compliant AI agent hub for financial tools integration",
        "mcp": {
            "protocol_version": config.mcp_protocol_version,
            "server_name": config.mcp_server_name,
            "server_version": config.mcp_server_version
        },
        "endpoints": {
            "mcp": "/mcp",
            "health": "/health",
            "services": "/api/v1/services",
            "tools": "/api/v1/tools"
        }
    }


if __name__ == "__main__":
    import uvicorn

    config = get_config()

    uvicorn.run(
        "main:app",
        host=config.host,
        port=config.port,
        reload=config.debug,
        log_level=config.log_level.lower()
    )