"""
Market Spoke - MCP Server for Market Analysis Tools
"""
import asyncio
import json
import sys
import os
from contextlib import asynccontextmanager
from typing import Any, Dict, List

# Add shared directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from shared.schemas.mcp_protocol import (
    InitializeRequest, InitializeResponse,
    ListToolsRequest, ListToolsResponse,
    CallToolRequest, CallToolResponse,
    Tool, CallToolResult
)
from shared.utils.logging import setup_logging
from shared.utils.consul_client import ConsulClient
from shared.utils.health_check import HealthChecker
from app.core.config import MarketSpokeConfig
from app.services.hub_registration import HubRegistrationService
from app.tools.price_analyzer import PriceAnalyzer
from app.tools.volatility_predictor import VolatilityPredictor
from app.tools.sentiment_analyzer import SentimentAnalyzer

# Initialize logger
logger = setup_logging("market-spoke")

# Global configuration
config = MarketSpokeConfig()

# Initialize tools
price_analyzer = PriceAnalyzer()
volatility_predictor = VolatilityPredictor()
sentiment_analyzer = SentimentAnalyzer()

# Tool registry
TOOLS_REGISTRY = {
    "market.get_price": price_analyzer,
    "market.predict_volatility": volatility_predictor,
    "market.analyze_sentiment": sentiment_analyzer
}


async def register_with_hub():
    """Register this Market Spoke with the Hub"""
    try:
        registration_service = HubRegistrationService()
        await registration_service.register()
        logger.info("Successfully registered with Hub")
    except Exception as e:
        logger.error(f"Failed to register with Hub: {e}")
        # Don't fail startup, just log the error


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Market Spoke MCP Server...")

    # Initialize Consul client
    consul_client = ConsulClient(
        host=config.consul_host,
        port=config.consul_port
    )
    app.state.consul = consul_client

    # Register with Hub
    await register_with_hub()

    # Register health checks
    health_checker = HealthChecker("market-spoke", "1.0.0")
    app.state.health_checker = health_checker

    logger.info("Market Spoke MCP Server started successfully")

    yield

    # Shutdown
    logger.info("Shutting down Market Spoke MCP Server...")

    # Deregister from Consul
    try:
        await consul_client.deregister_service(config.service_name)
        logger.info("Deregistered from Consul")
    except Exception as e:
        logger.error(f"Failed to deregister from Consul: {e}")


# FastAPI application
app = FastAPI(
    title="Market Spoke MCP Server",
    description="MCP Server for Market Analysis Tools",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint - service information"""
    return {
        "service": "market-spoke",
        "version": "1.0.0",
        "status": "running",
        "tools": list(TOOLS_REGISTRY.keys())
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    health_checker = getattr(app.state, 'health_checker', None)
    if not health_checker:
        return {"status": "healthy", "timestamp": datetime.utcnow().isoformat(), "checks": []}

    result = await health_checker.check_all()

    return {
        "status": result.status.value,
        "timestamp": result.timestamp.isoformat(),
        "checks": [check.to_dict() for check in result.checks],
        "service": "market-spoke"
    }


@app.post("/mcp")
async def mcp_endpoint(request: Dict[str, Any]):
    """Main MCP JSON-RPC endpoint"""
    try:
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        logger.info(f"MCP request: {method}")

        if method == "initialize":
            # Parse initialize request
            init_request = InitializeRequest(**params)

            # Create response
            response = InitializeResponse(
                protocolVersion="2024-11-05",
                capabilities={
                    "tools": {},
                    "logging": {}
                },
                serverInfo={
                    "name": "market-spoke",
                    "version": "1.0.0"
                }
            )

            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": response.dict()
            }

        elif method == "tools/list":
            # Parse list tools request
            list_request = ListToolsRequest(**params) if params else ListToolsRequest()

            # Get tools list
            tools = []
            for tool_id in TOOLS_REGISTRY:
                tool_handler = TOOLS_REGISTRY[tool_id]
                tool_info = await tool_handler.get_tool_info()
                tools.append(Tool(**tool_info))

            response = ListToolsResponse(tools=tools)

            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": response.dict()
            }

        elif method == "tools/call":
            # Parse call tool request
            call_request = CallToolRequest(**params)

            # Get tool handler
            tool_id = call_request.name
            if tool_id not in TOOLS_REGISTRY:
                raise ValueError(f"Tool not found: {tool_id}")

            tool_handler = TOOLS_REGISTRY[tool_id]

            # Execute tool
            result = await tool_handler.execute(call_request.arguments or {})

            # Create response
            tool_result = CallToolResult(
                content=[{
                    "type": "text",
                    "text": json.dumps(result, indent=2)
                }]
            )

            response = CallToolResponse(content=tool_result.content)

            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": response.dict()
            }

        else:
            raise ValueError(f"Unknown method: {method}")

    except Exception as e:
        logger.error(f"MCP request failed: {e}")

        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "error": {
                "code": -32603,
                "message": str(e)
            }
        }


@app.get("/tools")
async def list_tools():
    """REST endpoint to list available tools"""
    tools = []
    for tool_id in TOOLS_REGISTRY:
        tool_handler = TOOLS_REGISTRY[tool_id]
        tool_info = await tool_handler.get_tool_info()
        tools.append(tool_info)

    return {"tools": tools}


@app.post("/tools/{tool_id}/execute")
async def execute_tool(tool_id: str, arguments: Dict[str, Any]):
    """REST endpoint to execute a specific tool"""
    if tool_id not in TOOLS_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Tool not found: {tool_id}")

    try:
        tool_handler = TOOLS_REGISTRY[tool_id]
        result = await tool_handler.execute(arguments)
        return {"result": result}
    except Exception as e:
        logger.error(f"Tool execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    # For MCP stdio mode
    if len(sys.argv) > 1 and sys.argv[1] == "mcp":
        # Run in MCP stdio mode
        async def mcp_stdio():
            while True:
                try:
                    line = input()
                    if not line:
                        break

                    request = json.loads(line)
                    response = await mcp_endpoint(request)
                    print(json.dumps(response))

                except EOFError:
                    break
                except Exception as e:
                    logger.error(f"MCP stdio error: {e}")

        asyncio.run(mcp_stdio())
    else:
        # Run as HTTP server
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=config.port,
            reload=config.debug
        )