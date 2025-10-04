#!/usr/bin/env python3
"""
Portfolio Spoke MCP Server - Professional Portfolio Management
Provides 8 comprehensive portfolio tools:
- Portfolio Optimizer, Portfolio Rebalancer
- Performance Analyzer, Backtester, Factor Analyzer
- Asset Allocator, Tax Optimizer, Portfolio Dashboard
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
dotenv_path = project_root.parent.parent / '.env'
if dotenv_path.exists():
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

# Import Portfolio Spoke tools
from app.tools.portfolio_optimizer import portfolio_optimizer
from app.tools.portfolio_rebalancer import portfolio_rebalancer
from app.tools.performance_analyzer import performance_analyzer
from app.tools.backtester import backtester
from app.tools.factor_analyzer import factor_analyzer
from app.tools.asset_allocator import asset_allocator
from app.tools.tax_optimizer import tax_optimizer
from app.tools.portfolio_dashboard import portfolio_dashboard

# Create MCP server
server = Server("fin-hub-portfolio")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available portfolio management tools (8 tools)"""
    return [
        # 1. Portfolio Optimizer
        types.Tool(
            name="portfolio_optimize",
            description="Optimize portfolio weights using Mean-Variance, HRP, Black-Litterman, or Risk Parity. Supports multiple objectives: max Sharpe, min volatility, efficient return/risk.",
            inputSchema={
                "type": "object",
                "properties": {
                    "tickers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of stock symbols (2-50 stocks)",
                        "minItems": 2,
                        "maxItems": 50
                    },
                    "method": {
                        "type": "string",
                        "enum": ["mean_variance", "hrp", "risk_parity", "max_sharpe", "min_volatility"],
                        "default": "mean_variance",
                        "description": "Optimization method"
                    },
                    "objective": {
                        "type": "string",
                        "enum": ["max_sharpe", "min_volatility", "efficient_return", "efficient_risk"],
                        "default": "max_sharpe",
                        "description": "Optimization objective (for mean_variance)"
                    },
                    "target_return": {
                        "type": "number",
                        "description": "Target annual return for efficient_return objective (e.g., 0.15 for 15%)"
                    },
                    "target_risk": {
                        "type": "number",
                        "description": "Target annual volatility for efficient_risk objective (e.g., 0.20 for 20%)"
                    },
                    "risk_free_rate": {
                        "type": "number",
                        "default": 0.03,
                        "description": "Risk-free rate (annualized, default: 3%)"
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date for historical data (YYYY-MM-DD, default: 1 year ago)"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date for historical data (YYYY-MM-DD, default: today)"
                    }
                },
                "required": ["tickers"]
            }
        ),

        # 2. Portfolio Rebalancer
        types.Tool(
            name="portfolio_rebalance",
            description="Generate rebalancing trades to align portfolio with target weights. Supports threshold-based, periodic, and tax-aware strategies.",
            inputSchema={
                "type": "object",
                "properties": {
                    "current_positions": {
                        "type": "object",
                        "description": "Current holdings: {ticker: {shares, value, price}}",
                        "additionalProperties": {
                            "type": "object",
                            "properties": {
                                "shares": {"type": "number"},
                                "value": {"type": "number"},
                                "price": {"type": "number"}
                            }
                        }
                    },
                    "target_weights": {
                        "type": "object",
                        "description": "Target allocation: {ticker: weight}",
                        "additionalProperties": {"type": "number"}
                    },
                    "total_value": {
                        "type": "number",
                        "description": "Total portfolio value"
                    },
                    "cash_available": {
                        "type": "number",
                        "default": 0,
                        "description": "Available cash for investing"
                    },
                    "strategy": {
                        "type": "string",
                        "enum": ["threshold", "periodic", "tax_aware"],
                        "default": "threshold",
                        "description": "Rebalancing strategy"
                    },
                    "threshold": {
                        "type": "number",
                        "default": 0.05,
                        "description": "Drift threshold (5% default)"
                    }
                },
                "required": ["current_positions", "target_weights", "total_value"]
            }
        ),

        # 3. Performance Analyzer
        types.Tool(
            name="portfolio_analyze_performance",
            description="Calculate comprehensive performance metrics: returns, Sharpe ratio, Sortino ratio, max drawdown, alpha/beta, and attribution analysis.",
            inputSchema={
                "type": "object",
                "properties": {
                    "positions": {
                        "type": "object",
                        "description": "Portfolio positions: {ticker: shares} or {ticker: weight}",
                        "additionalProperties": {"type": "number"}
                    },
                    "benchmark": {
                        "type": "string",
                        "default": "SPY",
                        "description": "Benchmark symbol (default: SPY)"
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Analysis start date (YYYY-MM-DD)"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "Analysis end date (YYYY-MM-DD)"
                    },
                    "risk_free_rate": {
                        "type": "number",
                        "default": 0.03,
                        "description": "Risk-free rate (annualized)"
                    }
                },
                "required": ["positions"]
            }
        ),

        # 4. Backtester
        types.Tool(
            name="portfolio_backtest",
            description="Backtest trading strategies with realistic transaction costs, slippage, and rebalancing. Supports buy-and-hold, momentum, mean-reversion strategies.",
            inputSchema={
                "type": "object",
                "properties": {
                    "tickers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of stock symbols"
                    },
                    "strategy": {
                        "type": "string",
                        "enum": ["buy_and_hold", "equal_weight", "momentum", "mean_reversion", "custom"],
                        "default": "equal_weight",
                        "description": "Trading strategy"
                    },
                    "initial_capital": {
                        "type": "number",
                        "default": 100000,
                        "description": "Initial capital (USD)"
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Backtest start date (YYYY-MM-DD)"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "Backtest end date (YYYY-MM-DD)"
                    },
                    "rebalance_frequency": {
                        "type": "string",
                        "enum": ["daily", "weekly", "monthly", "quarterly", "yearly"],
                        "default": "monthly",
                        "description": "Rebalancing frequency"
                    },
                    "transaction_cost": {
                        "type": "number",
                        "default": 0.001,
                        "description": "Transaction cost (0.001 = 0.1%)"
                    }
                },
                "required": ["tickers"]
            }
        ),

        # 5. Factor Analyzer
        types.Tool(
            name="portfolio_analyze_factors",
            description="Perform multi-factor analysis (Fama-French 5-factor, momentum, quality). Explains portfolio returns through factor exposures.",
            inputSchema={
                "type": "object",
                "properties": {
                    "tickers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of stock symbols"
                    },
                    "weights": {
                        "type": "object",
                        "description": "Portfolio weights: {ticker: weight}",
                        "additionalProperties": {"type": "number"}
                    },
                    "factors": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["market", "size", "value", "profitability", "investment", "momentum", "quality"]
                        },
                        "default": ["market", "size", "value"],
                        "description": "Factor models to analyze"
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Analysis start date (YYYY-MM-DD)"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "Analysis end date (YYYY-MM-DD)"
                    }
                },
                "required": ["tickers"]
            }
        ),

        # 6. Asset Allocator
        types.Tool(
            name="portfolio_allocate_assets",
            description="Determine strategic asset allocation across stocks, bonds, commodities, cash. Supports age-based, risk-based, and goals-based strategies.",
            inputSchema={
                "type": "object",
                "properties": {
                    "total_capital": {
                        "type": "number",
                        "description": "Total capital to allocate (USD)"
                    },
                    "strategy": {
                        "type": "string",
                        "enum": ["age_based", "risk_based", "goals_based", "all_weather", "tactical"],
                        "default": "risk_based",
                        "description": "Allocation strategy"
                    },
                    "risk_tolerance": {
                        "type": "string",
                        "enum": ["conservative", "moderate", "aggressive"],
                        "default": "moderate",
                        "description": "Risk tolerance level"
                    },
                    "age": {
                        "type": "number",
                        "description": "Investor age (for age_based strategy)"
                    },
                    "time_horizon": {
                        "type": "number",
                        "description": "Investment time horizon in years"
                    },
                    "constraints": {
                        "type": "object",
                        "description": "Allocation constraints",
                        "properties": {
                            "min_stocks": {"type": "number"},
                            "max_stocks": {"type": "number"},
                            "min_bonds": {"type": "number"},
                            "max_bonds": {"type": "number"}
                        }
                    }
                },
                "required": ["total_capital"]
            }
        ),

        # 7. Tax Optimizer
        types.Tool(
            name="portfolio_optimize_taxes",
            description="Tax-loss harvesting recommendations, minimize capital gains tax, optimize holding periods. Considers short/long-term rates and wash sale rules.",
            inputSchema={
                "type": "object",
                "properties": {
                    "positions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "ticker": {"type": "string"},
                                "shares": {"type": "number"},
                                "purchase_date": {"type": "string"},
                                "purchase_price": {"type": "number"},
                                "current_price": {"type": "number"}
                            }
                        },
                        "description": "Current positions with purchase info"
                    },
                    "target_allocation": {
                        "type": "object",
                        "description": "Desired target allocation: {ticker: weight}",
                        "additionalProperties": {"type": "number"}
                    },
                    "tax_rates": {
                        "type": "object",
                        "properties": {
                            "short_term": {
                                "type": "number",
                                "default": 0.37,
                                "description": "Short-term capital gains rate"
                            },
                            "long_term": {
                                "type": "number",
                                "default": 0.20,
                                "description": "Long-term capital gains rate"
                            }
                        }
                    },
                    "max_tax_impact": {
                        "type": "number",
                        "description": "Maximum acceptable tax impact (USD)"
                    }
                },
                "required": ["positions"]
            }
        ),

        # 8. Portfolio Dashboard
        types.Tool(
            name="portfolio_generate_dashboard",
            description="Generate comprehensive portfolio summary: current allocation, performance, risk metrics, top holdings, sector exposure, and recommendations.",
            inputSchema={
                "type": "object",
                "properties": {
                    "positions": {
                        "type": "object",
                        "description": "Current positions: {ticker: shares} or {ticker: weight}",
                        "additionalProperties": {"type": "number"}
                    },
                    "benchmark": {
                        "type": "string",
                        "default": "SPY",
                        "description": "Benchmark for comparison"
                    },
                    "include_recommendations": {
                        "type": "boolean",
                        "default": True,
                        "description": "Include optimization recommendations"
                    },
                    "risk_free_rate": {
                        "type": "number",
                        "default": 0.03,
                        "description": "Risk-free rate for metrics"
                    }
                },
                "required": ["positions"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool execution (8 tools)"""
    import json

    arguments = arguments or {}

    try:
        # Route to appropriate tool
        if name == "portfolio_optimize":
            result = await portfolio_optimizer(**arguments)
        elif name == "portfolio_rebalance":
            result = await portfolio_rebalancer(**arguments)
        elif name == "portfolio_analyze_performance":
            result = await performance_analyzer(**arguments)
        elif name == "portfolio_backtest":
            result = await backtester(**arguments)
        elif name == "portfolio_analyze_factors":
            result = await factor_analyzer(**arguments)
        elif name == "portfolio_allocate_assets":
            result = await asset_allocator(**arguments)
        elif name == "portfolio_optimize_taxes":
            result = await tax_optimizer(**arguments)
        elif name == "portfolio_generate_dashboard":
            result = await portfolio_dashboard(**arguments)
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
