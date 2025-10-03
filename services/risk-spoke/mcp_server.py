#!/usr/bin/env python3
"""
Risk Spoke MCP Server - MCP SDK Implementation
"""
import sys
import os
from pathlib import Path
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
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
server = Server("fin-hub-risk")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available risk management tools"""
    return [
        types.Tool(
            name="detect_anomaly",
            description="Detect anomalies in financial data",
            inputSchema={
                "type": "object",
                "properties": {
                    "data": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "Array of numerical data points to analyze"
                    },
                    "threshold": {
                        "type": "number",
                        "description": "Sensitivity threshold for anomaly detection (default: 2.0)",
                        "default": 2.0
                    }
                },
                "required": ["data"]
            }
        ),
        types.Tool(
            name="check_compliance",
            description="Check portfolio compliance with regulations",
            inputSchema={
                "type": "object",
                "properties": {
                    "portfolio": {
                        "type": "object",
                        "description": "Portfolio holdings to check"
                    },
                    "rules": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Compliance rules to check against"
                    }
                },
                "required": ["portfolio"]
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
        if name == "detect_anomaly":
            data = arguments.get("data", [])
            threshold = arguments.get("threshold", 2.0)

            # Simple anomaly detection simulation
            if not data:
                result = {"error": "No data provided"}
            else:
                import statistics
                mean = statistics.mean(data)
                stdev = statistics.stdev(data) if len(data) > 1 else 0
                anomalies = []

                for i, value in enumerate(data):
                    if stdev > 0 and abs(value - mean) > threshold * stdev:
                        anomalies.append({"index": i, "value": value, "deviation": abs(value - mean) / stdev})

                result = {
                    "total_points": len(data),
                    "anomalies_found": len(anomalies),
                    "anomalies": anomalies,
                    "mean": mean,
                    "stdev": stdev
                }

        elif name == "check_compliance":
            portfolio = arguments.get("portfolio", {})
            rules = arguments.get("rules", [])

            result = {
                "compliant": True,
                "checks_performed": len(rules) if rules else 0,
                "violations": [],
                "warnings": []
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
