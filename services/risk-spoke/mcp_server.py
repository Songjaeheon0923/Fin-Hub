#!/usr/bin/env python3
"""
Risk Spoke MCP Server - Quantitative Risk Management
Provides VaR, risk metrics, and portfolio analysis tools
"""
import sys
import os
from pathlib import Path
import logging

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
dotenv_path = project_root.parent / '.env'
if dotenv_path.exists():
    load_dotenv(dotenv_path)

# Configure logging to stderr ONLY (MCP requires stdout for protocol)
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr,
    force=True
)

# Disable all existing loggers that might write to stdout
for logger_name in logging.root.manager.loggerDict:
    logger = logging.getLogger(logger_name)
    logger.handlers = []
    logger.addHandler(logging.StreamHandler(sys.stderr))
    logger.setLevel(logging.WARNING)

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
import mcp.server.stdio
import mcp.types as types

# Import Risk Spoke tools
from app.tools.var_calculator import VaRCalculatorTool
from app.tools.risk_metrics import RiskMetricsTool
from app.tools.portfolio_risk import PortfolioRiskTool

# Create MCP server
server = Server("fin-hub-risk")

# Initialize tool instances
var_tool = VaRCalculatorTool()
metrics_tool = RiskMetricsTool()
portfolio_tool = PortfolioRiskTool()


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available risk management tools"""
    # Get tool info from each tool instance
    var_info = await var_tool.get_tool_info()
    metrics_info = await metrics_tool.get_tool_info()
    portfolio_info = await portfolio_tool.get_tool_info()

    return [
        types.Tool(
            name=var_info["name"],
            description=var_info["description"],
            inputSchema=var_info["inputSchema"]
        ),
        types.Tool(
            name=metrics_info["name"],
            description=metrics_info["description"],
            inputSchema=metrics_info["inputSchema"]
        ),
        types.Tool(
            name=portfolio_info["name"],
            description=portfolio_info["description"],
            inputSchema=portfolio_info["inputSchema"]
        )
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool execution"""
    import json

    arguments = arguments or {}

    try:
        # Route to appropriate tool
        if name == "risk.calculate_var":
            result = await var_tool.execute(arguments)
        elif name == "risk.calculate_metrics":
            result = await metrics_tool.execute(arguments)
        elif name == "risk.analyze_portfolio":
            result = await portfolio_tool.execute(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    except Exception as e:
        logging.error(f"Error executing {name}: {str(e)}", exc_info=True)
        return [types.TextContent(
            type="text",
            text=json.dumps({"error": f"Tool execution failed: {str(e)}"}, indent=2)
        )]


async def main():
    """Run the MCP server"""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="fin-hub-risk",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                )
            )
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
