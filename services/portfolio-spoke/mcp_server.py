"""
Portfolio Spoke MCP Server

Exposes portfolio management tools via Model Context Protocol (MCP).

MCP Tools (Phase 1 - Week 1-2):
1. portfolio_optimizer - Portfolio optimization
2. portfolio_rebalancer - Rebalancing trades

Future tools (Phase 1 - Week 3-6):
3. performance_analyzer - Performance metrics
4. backtester - Strategy backtesting
5. factor_analyzer - Factor analysis
6. asset_allocator - Asset allocation
7. tax_optimizer - Tax optimization
8. portfolio_dashboard - Dashboard summary

Usage:
    python mcp_server.py  # Run as stdio server
"""

import asyncio
import json
import sys
import logging
from typing import Any, Dict
from pathlib import Path

# Add app directory to path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

from tools.portfolio_optimizer import portfolio_optimizer
from tools.portfolio_rebalancer import portfolio_rebalancer
from tools.performance_analyzer import performance_analyzer
from tools.backtester import backtester
from tools.factor_analyzer import factor_analyzer
from tools.asset_allocator import asset_allocator
from tools.tax_optimizer import tax_optimizer
from tools.portfolio_dashboard import portfolio_dashboard

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('portfolio_spoke_mcp.log'),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)


class MCPServer:
    """Model Context Protocol Server for Portfolio Spoke"""

    def __init__(self):
        self.tools = {
            "portfolio_optimizer": portfolio_optimizer,
            "portfolio_rebalancer": portfolio_rebalancer,
            "performance_analyzer": performance_analyzer,
            "backtester": backtester,
            "factor_analyzer": factor_analyzer,
            "asset_allocator": asset_allocator,
            "tax_optimizer": tax_optimizer,
            "portfolio_dashboard": portfolio_dashboard
        }

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle incoming MCP request.

        Args:
            request: JSON-RPC request
                {
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "portfolio_optimizer",
                        "arguments": {
                            "tickers": ["AAPL", "MSFT"],
                            "method": "mean_variance",
                            ...
                        }
                    },
                    "id": 1
                }

        Returns:
            JSON-RPC response
        """
        try:
            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")

            logger.info(f"Received request: method={method}, id={request_id}")

            if method == "tools/list":
                # List available tools
                response = self._list_tools()
            elif method == "tools/call":
                # Call a specific tool
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                response = await self._call_tool(tool_name, arguments)
            else:
                response = {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    },
                    "id": request_id
                }
                return response

            # Success response
            return {
                "jsonrpc": "2.0",
                "result": response,
                "id": request_id
            }

        except Exception as e:
            logger.error(f"Error handling request: {str(e)}", exc_info=True)
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                },
                "id": request.get("id")
            }

    def _list_tools(self) -> Dict[str, Any]:
        """
        List all available tools.

        Returns:
            {
                "tools": [
                    {
                        "name": "portfolio_optimizer",
                        "description": "...",
                        "inputSchema": {...}
                    },
                    ...
                ]
            }
        """
        tools_list = [
            {
                "name": "portfolio_optimizer",
                "description": "Optimize portfolio weights using Mean-Variance, HRP, Black-Litterman, or Risk Parity",
                "inputSchema": {
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
                            "enum": ["mean_variance", "hrp", "black_litterman", "risk_parity", "max_sharpe", "min_volatility"],
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
                            "description": "Target return for efficient_return objective"
                        },
                        "target_risk": {
                            "type": "number",
                            "description": "Target risk for efficient_risk objective"
                        },
                        "risk_free_rate": {
                            "type": "number",
                            "default": 0.03,
                            "description": "Risk-free rate (annualized)"
                        }
                    },
                    "required": ["tickers"]
                }
            },
            {
                "name": "portfolio_rebalancer",
                "description": "Generate rebalancing trades to align portfolio with target weights",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "current_positions": {
                            "type": "object",
                            "description": "Current holdings {ticker: {shares, value, price}}",
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
                            "description": "Target allocation {ticker: weight}",
                            "additionalProperties": {"type": "number"}
                        },
                        "total_value": {
                            "type": "number",
                            "description": "Total portfolio value"
                        },
                        "cash_available": {
                            "type": "number",
                            "default": 0,
                            "description": "Available cash"
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
            }
        ]

        return {"tools": tools_list}

    async def _call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a specific tool.

        Args:
            tool_name: Name of the tool
            arguments: Tool arguments

        Returns:
            Tool result
        """
        if tool_name not in self.tools:
            raise ValueError(f"Unknown tool: {tool_name}")

        tool_func = self.tools[tool_name]

        logger.info(f"Calling tool: {tool_name} with args: {list(arguments.keys())}")

        # Call the tool
        result = await tool_func(**arguments)

        logger.info(f"Tool {tool_name} completed successfully")

        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(result, indent=2)
                }
            ]
        }

    async def run(self):
        """
        Run MCP server in stdio mode.

        Reads JSON-RPC requests from stdin and writes responses to stdout.
        """
        logger.info("Portfolio Spoke MCP Server starting...")
        logger.info(f"Available tools: {list(self.tools.keys())}")

        # Read from stdin line by line
        while True:
            try:
                line = sys.stdin.readline()

                if not line:
                    # EOF reached
                    logger.info("EOF reached, shutting down")
                    break

                line = line.strip()
                if not line:
                    continue

                # Parse JSON request
                try:
                    request = json.loads(line)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON: {e}")
                    continue

                # Handle request
                response = await self.handle_request(request)

                # Write response to stdout
                print(json.dumps(response), flush=True)

            except KeyboardInterrupt:
                logger.info("Keyboard interrupt, shutting down")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {str(e)}", exc_info=True)


async def main():
    """Main entry point"""
    server = MCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
