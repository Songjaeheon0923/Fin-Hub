#!/usr/bin/env python3
"""
Market Spoke MCP Server - MCP SDK Implementation
"""
import sys
import os
from pathlib import Path
import logging

# CRITICAL: Disable ALL stdout output before any imports
# MCP protocol uses stdout exclusively for JSON-RPC communication
class StderrOnly:
    """Redirect all print/stdout to stderr"""
    def write(self, text):
        sys.stderr.write(text)
    def flush(self):
        sys.stderr.flush()

# Replace stdout with stderr redirect
sys.stdout = StderrOnly()

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables (suppress all output)
from dotenv import load_dotenv
dotenv_path = project_root / '.env'
load_dotenv(dotenv_path)

# Configure logging to stderr ONLY
logging.basicConfig(
    level=logging.CRITICAL,  # Only critical errors
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr,
    force=True
)

# Disable ALL loggers
logging.disable(logging.CRITICAL)

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
import mcp.server.stdio
import mcp.types as types

# Import tool handlers
# Add services directory to path
sys.path.insert(0, str(project_root / 'services' / 'market-spoke'))

from app.tools.unified_market_data import (
    UnifiedMarketDataTool,
    StockQuoteTool,
    CryptoPriceTool,
    FinancialNewsTool,
    EconomicIndicatorTool,
    MarketOverviewTool,
    APIStatusTool
)

# Create MCP server
server = Server("fin-hub-market")

# Tool instances
unified_tool = UnifiedMarketDataTool()
stock_quote_tool = StockQuoteTool()
crypto_tool = CryptoPriceTool()
news_tool = FinancialNewsTool()
economic_tool = EconomicIndicatorTool()
overview_tool = MarketOverviewTool()
status_tool = APIStatusTool()


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available market data tools"""
    return [
        types.Tool(
            name="unified_market_data",
            description="Get comprehensive market data from multiple sources with automatic fallback",
            inputSchema={
                "type": "object",
                "properties": {
                    "query_type": {
                        "type": "string",
                        "description": "Type of market data",
                        "enum": ["stock_quote", "crypto_price", "news", "economic", "overview"]
                    },
                    "symbol": {
                        "type": "string",
                        "description": "Stock/crypto symbol (e.g., AAPL, BTC)"
                    },
                    "query": {
                        "type": "string",
                        "description": "Search query for news"
                    },
                    "indicator": {
                        "type": "string",
                        "description": "Economic indicator code (e.g., GDP, CPI)"
                    }
                },
                "required": ["query_type"]
            }
        ),
        types.Tool(
            name="stock_quote",
            description="Get real-time stock quote data",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock ticker symbol (e.g., AAPL, MSFT, GOOGL)"
                    }
                },
                "required": ["symbol"]
            }
        ),
        types.Tool(
            name="crypto_price",
            description="Get cryptocurrency price data",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Cryptocurrency symbol (e.g., BTC, ETH)"
                    }
                },
                "required": ["symbol"]
            }
        ),
        types.Tool(
            name="financial_news",
            description="Get latest financial news",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "News search query (e.g., 'Tesla earnings', 'Fed interest rates')"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of news articles to return (default: 10)",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="economic_indicator",
            description="Get economic indicator data",
            inputSchema={
                "type": "object",
                "properties": {
                    "indicator": {
                        "type": "string",
                        "description": "Economic indicator code (e.g., GDP, CPI, UNRATE)"
                    }
                },
                "required": ["indicator"]
            }
        ),
        types.Tool(
            name="market_overview",
            description="Get comprehensive market overview including major indices",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        types.Tool(
            name="api_status",
            description="Check status and availability of all data provider APIs",
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
        if name == "unified_market_data":
            result = await unified_tool.execute(arguments)
        elif name == "stock_quote":
            result = await stock_quote_tool.execute(arguments)
        elif name == "crypto_price":
            result = await crypto_tool.execute(arguments)
        elif name == "financial_news":
            result = await news_tool.execute(arguments)
        elif name == "economic_indicator":
            result = await economic_tool.execute(arguments)
        elif name == "market_overview":
            result = await overview_tool.execute(arguments)
        elif name == "api_status":
            result = await status_tool.execute(arguments)
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
    # Import original stdout/stdin for MCP communication
    import sys
    original_stdin = sys.__stdin__
    original_stdout = sys.__stdout__

    # Temporarily restore stdout for MCP SDK
    sys.stdin = original_stdin
    sys.stdout = original_stdout

    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="fin-hub-market",
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
