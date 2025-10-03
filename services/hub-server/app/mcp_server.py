#!/usr/bin/env python3
"""
Hub Server MCP Server - MCP SDK Implementation
"""
import sys
import os
from pathlib import Path
import logging

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
dotenv_path = project_root / '.env'
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

# Create MCP server
server = Server("fin-hub")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available hub management tools"""
    return [
        types.Tool(
            name="hub_status",
            description="Get hub server status and registered spokes",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        types.Tool(
            name="list_spokes",
            description="List all registered spoke services",
            inputSchema={
                "type": "object",
                "properties": {}
            }
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
        if name == "hub_status":
            result = {
                "status": "running",
                "service": "fin-hub",
                "version": "1.0.0"
            }
        elif name == "list_spokes":
            result = {
                "spokes": [
                    {"name": "market-spoke", "status": "registered"},
                    {"name": "risk-spoke", "status": "registered"},
                    {"name": "pfolio-spoke", "status": "registered"}
                ]
            }
        else:
            raise ValueError(f"Unknown tool: {name}")

        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"Error executing {name}: {str(e)}"
        )]


async def main():
    """Run the MCP server"""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="fin-hub",
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
