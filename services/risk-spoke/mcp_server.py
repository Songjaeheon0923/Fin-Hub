#!/usr/bin/env python3
"""
Risk Spoke MCP Server - Quantitative Risk Management
Provides 8 comprehensive risk analysis tools:
- VaR Calculator, Risk Metrics, Portfolio Risk
- Stress Testing, Tail Risk Analysis, Greeks Calculator
- Compliance Checker, Risk Dashboard
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

# Import Risk Spoke tools
from app.tools.var_calculator import VaRCalculatorTool
from app.tools.risk_metrics import RiskMetricsTool
from app.tools.portfolio_risk import PortfolioRiskTool
from app.tools.stress_testing import StressTestingTool
from app.tools.tail_risk import TailRiskTool
from app.tools.greeks_calculator import GreeksCalculatorTool
from app.tools.compliance_checker import ComplianceCheckerTool
from app.tools.risk_dashboard import RiskDashboardTool

# Create MCP server
server = Server("fin-hub-risk")

# Initialize tool instances (8 tools total)
var_tool = VaRCalculatorTool()
metrics_tool = RiskMetricsTool()
portfolio_tool = PortfolioRiskTool()
stress_tool = StressTestingTool()
tail_tool = TailRiskTool()
greeks_tool = GreeksCalculatorTool()
compliance_tool = ComplianceCheckerTool()
dashboard_tool = RiskDashboardTool()


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available risk management tools (8 tools)"""
    # Get tool info from each tool instance
    var_info = await var_tool.get_tool_info()
    metrics_info = await metrics_tool.get_tool_info()
    portfolio_info = await portfolio_tool.get_tool_info()
    stress_info = await stress_tool.get_tool_info()
    tail_info = await tail_tool.get_tool_info()
    greeks_info = await greeks_tool.get_tool_info()
    compliance_info = await compliance_tool.get_tool_info()
    dashboard_info = await dashboard_tool.get_tool_info()

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
        ),
        types.Tool(
            name=stress_info["name"],
            description=stress_info["description"],
            inputSchema=stress_info["inputSchema"]
        ),
        types.Tool(
            name=tail_info["name"],
            description=tail_info["description"],
            inputSchema=tail_info["inputSchema"]
        ),
        types.Tool(
            name=greeks_info["name"],
            description=greeks_info["description"],
            inputSchema=greeks_info["inputSchema"]
        ),
        types.Tool(
            name=compliance_info["name"],
            description=compliance_info["description"],
            inputSchema=compliance_info["inputSchema"]
        ),
        types.Tool(
            name=dashboard_info["name"],
            description=dashboard_info["description"],
            inputSchema=dashboard_info["inputSchema"]
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
        if name == "risk_calculate_var":
            result = await var_tool.execute(arguments)
        elif name == "risk_calculate_metrics":
            result = await metrics_tool.execute(arguments)
        elif name == "risk_analyze_portfolio":
            result = await portfolio_tool.execute(arguments)
        elif name == "risk_stress_test":
            result = await stress_tool.execute(arguments)
        elif name == "risk_analyze_tail_risk":
            result = await tail_tool.execute(arguments)
        elif name == "risk_calculate_greeks":
            result = await greeks_tool.execute(arguments)
        elif name == "risk_check_compliance":
            result = await compliance_tool.execute(arguments)
        elif name == "risk_generate_dashboard":
            result = await dashboard_tool.execute(arguments)
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
