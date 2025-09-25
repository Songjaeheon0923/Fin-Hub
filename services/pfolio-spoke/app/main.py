"""
Portfolio Spoke - MCP Server for Portfolio Management Tools
"""
import asyncio
import json
import sys
import math
from contextlib import asynccontextmanager
from typing import Any, Dict, List

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import PortfolioSpokeConfig
from app.services.hub_registration import HubRegistrationService
from app.tools.portfolio_optimizer import PortfolioOptimizer
from app.tools.rebalancer import Rebalancer
from app.tools.consumption_analyzer import ConsumptionAnalyzer

# Global configuration
config = PortfolioSpokeConfig()

# Initialize tools
portfolio_optimizer = PortfolioOptimizer()
rebalancer = Rebalancer()
consumption_analyzer = ConsumptionAnalyzer()

# Tool registry
TOOLS_REGISTRY = {
    "pfolio.generate_optimal": portfolio_optimizer,
    "pfolio.rebalance_trigger": rebalancer,
    "pfolio.analyze_consumption": consumption_analyzer
}

# MCP Protocol Types
class InitializeRequest:
    def __init__(self, **kwargs):
        self.protocolVersion = kwargs.get("protocolVersion")
        self.capabilities = kwargs.get("capabilities", {})
        self.clientInfo = kwargs.get("clientInfo", {})

class ListToolsRequest:
    def __init__(self, **kwargs):
        pass

class CallToolRequest:
    def __init__(self, **kwargs):
        self.name = kwargs["name"]
        self.arguments = kwargs.get("arguments", {})

async def register_with_hub():
    """Register this Portfolio Spoke with the Hub"""
    try:
        registration_service = HubRegistrationService()
        await registration_service.register()
        print("Successfully registered with Hub")
    except Exception as e:
        print(f"Failed to register with Hub: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("Starting Portfolio Spoke MCP Server...")

    # Register with Hub
    await register_with_hub()

    print("Portfolio Spoke MCP Server started successfully")

    yield

    # Shutdown
    print("Shutting down Portfolio Spoke MCP Server...")

# FastAPI application
app = FastAPI(
    title="Portfolio Spoke MCP Server",
    description="MCP Server for Portfolio Management Tools",
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
        "service": "pfolio-spoke",
        "version": "1.0.0",
        "status": "running",
        "tools": list(TOOLS_REGISTRY.keys())
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "pfolio-spoke",
        "tools_available": len(TOOLS_REGISTRY),
        "timestamp": "2024-01-01T00:00:00Z"
    }

@app.post("/mcp")
async def mcp_endpoint(request: Dict[str, Any]):
    """Main MCP JSON-RPC endpoint"""
    try:
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        print(f"MCP request: {method}")

        if method == "initialize":
            # Create response
            response = {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "logging": {}
                },
                "serverInfo": {
                    "name": "pfolio-spoke",
                    "version": "1.0.0"
                }
            }

            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": response
            }

        elif method == "tools/list":
            # Get tools list
            tools = []
            for tool_id in TOOLS_REGISTRY:
                tool_handler = TOOLS_REGISTRY[tool_id]
                tool_info = await tool_handler.get_tool_info()
                tools.append(tool_info)

            response = {"tools": tools}

            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": response
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
            response = {
                "content": [{
                    "type": "text",
                    "text": json.dumps(result, indent=2)
                }]
            }

            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": response
            }

        else:
            raise ValueError(f"Unknown method: {method}")

    except Exception as e:
        print(f"MCP request failed: {e}")

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
        print(f"Tool execution failed: {e}")
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
                    print(f"MCP stdio error: {e}")

        asyncio.run(mcp_stdio())
    else:
        # Run as HTTP server
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=config.port,
            reload=False
        )