#!/usr/bin/env python3
"""
Portfolio Spoke MCP Server - MCP SDK Implementation
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
server = Server("fin-hub-portfolio")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available portfolio management tools"""
    return [
        types.Tool(
            name="optimize_portfolio",
            description="Generate optimal portfolio allocation based on risk/return preferences",
            inputSchema={
                "type": "object",
                "properties": {
                    "assets": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "symbol": {"type": "string"},
                                "expected_return": {"type": "number"},
                                "risk": {"type": "number"}
                            }
                        },
                        "description": "List of assets with expected returns and risk metrics"
                    },
                    "risk_tolerance": {
                        "type": "string",
                        "enum": ["conservative", "moderate", "aggressive"],
                        "description": "Risk tolerance level",
                        "default": "moderate"
                    },
                    "total_amount": {
                        "type": "number",
                        "description": "Total amount to invest",
                        "default": 10000
                    }
                },
                "required": ["assets"]
            }
        ),
        types.Tool(
            name="rebalance_portfolio",
            description="Calculate rebalancing actions needed to match target allocation",
            inputSchema={
                "type": "object",
                "properties": {
                    "current_holdings": {
                        "type": "object",
                        "description": "Current portfolio holdings {symbol: quantity}"
                    },
                    "target_allocation": {
                        "type": "object",
                        "description": "Target allocation percentages {symbol: percentage}"
                    },
                    "current_prices": {
                        "type": "object",
                        "description": "Current market prices {symbol: price}"
                    }
                },
                "required": ["current_holdings", "target_allocation", "current_prices"]
            }
        ),
        types.Tool(
            name="analyze_performance",
            description="Analyze portfolio performance metrics",
            inputSchema={
                "type": "object",
                "properties": {
                    "holdings": {
                        "type": "object",
                        "description": "Portfolio holdings {symbol: {quantity, purchase_price}}"
                    },
                    "current_prices": {
                        "type": "object",
                        "description": "Current market prices {symbol: price}"
                    }
                },
                "required": ["holdings", "current_prices"]
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
        if name == "optimize_portfolio":
            assets = arguments.get("assets", [])
            risk_tolerance = arguments.get("risk_tolerance", "moderate")
            total_amount = arguments.get("total_amount", 10000)

            if not assets:
                result = {"error": "No assets provided"}
            else:
                # Simple equal-weight allocation (placeholder)
                allocation = {}
                weight = 1.0 / len(assets)
                for asset in assets:
                    symbol = asset.get("symbol")
                    allocation[symbol] = {
                        "weight": weight,
                        "amount": total_amount * weight
                    }

                result = {
                    "risk_tolerance": risk_tolerance,
                    "total_amount": total_amount,
                    "allocation": allocation,
                    "diversification_score": min(len(assets) * 0.2, 1.0)
                }

        elif name == "rebalance_portfolio":
            current = arguments.get("current_holdings", {})
            target = arguments.get("target_allocation", {})
            prices = arguments.get("current_prices", {})

            # Calculate current value
            total_value = sum(current.get(s, 0) * prices.get(s, 0) for s in current)

            # Calculate rebalancing actions
            actions = []
            for symbol, target_pct in target.items():
                current_qty = current.get(symbol, 0)
                current_value = current_qty * prices.get(symbol, 0)
                current_pct = current_value / total_value if total_value > 0 else 0

                target_value = total_value * target_pct
                target_qty = target_value / prices.get(symbol, 1) if prices.get(symbol) else 0

                diff_qty = target_qty - current_qty

                if abs(diff_qty) > 0.01:
                    actions.append({
                        "symbol": symbol,
                        "action": "buy" if diff_qty > 0 else "sell",
                        "quantity": abs(diff_qty),
                        "current_allocation": current_pct,
                        "target_allocation": target_pct
                    })

            result = {
                "total_portfolio_value": total_value,
                "rebalancing_actions": actions,
                "number_of_actions": len(actions)
            }

        elif name == "analyze_performance":
            holdings = arguments.get("holdings", {})
            prices = arguments.get("current_prices", {})

            total_cost = 0
            total_value = 0
            positions = []

            for symbol, holding in holdings.items():
                qty = holding.get("quantity", 0)
                purchase_price = holding.get("purchase_price", 0)
                current_price = prices.get(symbol, purchase_price)

                cost = qty * purchase_price
                value = qty * current_price
                gain_loss = value - cost
                gain_loss_pct = (gain_loss / cost * 100) if cost > 0 else 0

                total_cost += cost
                total_value += value

                positions.append({
                    "symbol": symbol,
                    "quantity": qty,
                    "purchase_price": purchase_price,
                    "current_price": current_price,
                    "cost_basis": cost,
                    "current_value": value,
                    "gain_loss": gain_loss,
                    "gain_loss_pct": gain_loss_pct
                })

            total_gain_loss = total_value - total_cost
            total_gain_loss_pct = (total_gain_loss / total_cost * 100) if total_cost > 0 else 0

            result = {
                "total_cost_basis": total_cost,
                "total_current_value": total_value,
                "total_gain_loss": total_gain_loss,
                "total_gain_loss_pct": total_gain_loss_pct,
                "positions": positions
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
                server_name="fin-hub-portfolio",
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
