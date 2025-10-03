#!/usr/bin/env python3
"""
Test Risk Spoke Tools
Tests VaR Calculator, Risk Metrics, and Portfolio Risk tools
"""

import sys
import os
from pathlib import Path
import asyncio

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "services" / "risk-spoke"))

# Configure UTF-8 output for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Suppress pandas warnings
import warnings
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=RuntimeWarning)

from app.tools.var_calculator import VaRCalculatorTool
from app.tools.risk_metrics import RiskMetricsTool
from app.tools.portfolio_risk import PortfolioRiskTool


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Print colored header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text:^80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.RESET}\n")


def print_result(test_name: str, success: bool, details: str = ""):
    """Print test result"""
    status = f"{Colors.GREEN}✓ PASS{Colors.RESET}" if success else f"{Colors.RED}✗ FAIL{Colors.RESET}"
    print(f"{status} - {test_name}")
    if details:
        print(f"  {Colors.YELLOW}{details}{Colors.RESET}")


async def test_var_calculator():
    """Test VaR Calculator Tool"""
    print_header("Testing VaR Calculator")

    tool = VaRCalculatorTool()
    results = []

    # Test 1: Historical VaR
    print(f"{Colors.BLUE}Test 1: Historical VaR for AAPL{Colors.RESET}")
    result = await tool.execute({
        "symbol": "AAPL",
        "method": "historical",
        "confidence_level": 0.95,
        "portfolio_value": 10000
    })

    success = "error" not in result and "methods" in result
    if success:
        var_usd = result["methods"]["historical"]["var_usd"]
        details = f"95% VaR: ${var_usd:,.2f}"
    else:
        details = result.get("error", "Unknown error")

    print_result("Historical VaR", success, details)
    results.append(success)

    # Test 2: All methods
    print(f"\n{Colors.BLUE}Test 2: All VaR methods for TSLA{Colors.RESET}")
    result = await tool.execute({
        "symbol": "TSLA",
        "method": "all",
        "confidence_level": 0.99,
        "portfolio_value": 50000
    })

    success = "error" not in result and len(result.get("methods", {})) == 3
    if success:
        methods = ", ".join(result["methods"].keys())
        details = f"Calculated: {methods}"
    else:
        details = result.get("error", "Unknown error")

    print_result("All VaR Methods", success, details)
    results.append(success)

    # Test 3: Monte Carlo with custom simulations
    print(f"\n{Colors.BLUE}Test 3: Monte Carlo VaR (1000 simulations){Colors.RESET}")
    result = await tool.execute({
        "symbol": "NVDA",
        "method": "monte_carlo",
        "simulations": 1000,
        "confidence_level": 0.95
    })

    success = "error" not in result and "monte_carlo" in result.get("methods", {})
    if success:
        mc_var = result["methods"]["monte_carlo"]["var_usd"]
        details = f"MC VaR: ${mc_var:,.2f}"
    else:
        details = result.get("error", "Unknown error")

    print_result("Monte Carlo VaR", success, details)
    results.append(success)

    return results


async def test_risk_metrics():
    """Test Risk Metrics Tool"""
    print_header("Testing Risk Metrics Calculator")

    tool = RiskMetricsTool()
    results = []

    # Test 1: Sharpe Ratio
    print(f"{Colors.BLUE}Test 1: Sharpe Ratio for MSFT{Colors.RESET}")
    result = await tool.execute({
        "symbol": "MSFT",
        "metrics": ["sharpe"],
        "period": 252
    })

    success = "error" not in result and "sharpe_ratio" in result.get("metrics", {})
    if success:
        sharpe = result["metrics"]["sharpe_ratio"]["value"]
        interp = result["metrics"]["sharpe_ratio"]["interpretation"]
        details = f"Sharpe: {sharpe:.2f} - {interp}"
    else:
        details = result.get("error", "Unknown error")

    print_result("Sharpe Ratio", success, details)
    results.append(success)

    # Test 2: All metrics
    print(f"\n{Colors.BLUE}Test 2: All metrics for GOOGL{Colors.RESET}")
    result = await tool.execute({
        "symbol": "GOOGL",
        "metrics": ["all"],
        "benchmark": "SPY",
        "period": 252
    })

    success = "error" not in result and len(result.get("metrics", {})) >= 5
    if success:
        metric_names = list(result["metrics"].keys())[:5]
        details = f"Calculated: {', '.join(metric_names)}"
    else:
        details = result.get("error", "Unknown error")

    print_result("All Risk Metrics", success, details)
    results.append(success)

    # Test 3: Beta and Alpha
    print(f"\n{Colors.BLUE}Test 3: Beta/Alpha vs MSFT for AAPL{Colors.RESET}")
    result = await tool.execute({
        "symbol": "AAPL",
        "metrics": ["beta", "alpha"],
        "benchmark": "MSFT"
    })

    success = "error" not in result and "beta" in result.get("metrics", {})
    if success:
        beta = result["metrics"]["beta"]["beta"]["value"]
        alpha = result["metrics"]["alpha"]["annual_percent"]
        details = f"Beta: {beta:.2f}, Alpha: {alpha:.2f}%"
    else:
        details = result.get("error", "Unknown error")

    print_result("Beta & Alpha", success, details)
    results.append(success)

    # Test 4: Maximum Drawdown
    print(f"\n{Colors.BLUE}Test 4: Maximum Drawdown for TSLA{Colors.RESET}")
    result = await tool.execute({
        "symbol": "TSLA",
        "metrics": ["drawdown"],
        "period": 500
    })

    success = "error" not in result and "max_drawdown" in result.get("metrics", {})
    if success:
        dd = result["metrics"]["max_drawdown"]["max_drawdown_percent"]
        details = f"Max Drawdown: {dd:.2f}%"
    else:
        details = result.get("error", "Unknown error")

    print_result("Maximum Drawdown", success, details)
    results.append(success)

    return results


async def test_portfolio_risk():
    """Test Portfolio Risk Analysis Tool"""
    print_header("Testing Portfolio Risk Analyzer")

    tool = PortfolioRiskTool()
    results = []

    # Test 1: Simple 2-asset portfolio
    print(f"{Colors.BLUE}Test 1: Two-asset portfolio (AAPL 60%, MSFT 40%){Colors.RESET}")
    result = await tool.execute({
        "portfolio": [
            {"symbol": "AAPL", "weight": 0.6},
            {"symbol": "MSFT", "weight": 0.4}
        ],
        "period": 252
    })

    success = "error" not in result and "metrics" in result
    if success:
        port_vol = result["metrics"]["risk"]["portfolio_volatility_annual"]
        sharpe = result["metrics"]["performance"]["sharpe_ratio"]
        details = f"Vol: {port_vol:.2f}%, Sharpe: {sharpe:.2f}"
    else:
        details = result.get("error", "Unknown error")

    print_result("Two-Asset Portfolio", success, details)
    results.append(success)

    # Test 2: Diversified portfolio
    print(f"\n{Colors.BLUE}Test 2: Diversified portfolio (5 assets){Colors.RESET}")
    result = await tool.execute({
        "portfolio": [
            {"symbol": "AAPL", "weight": 0.25},
            {"symbol": "MSFT", "weight": 0.25},
            {"symbol": "GOOGL", "weight": 0.20},
            {"symbol": "NVDA", "weight": 0.15},
            {"symbol": "TSLA", "weight": 0.15}
        ],
        "period": 252,
        "confidence_level": 0.95
    })

    success = "error" not in result and "diversification" in result.get("metrics", {})
    if success:
        div_ratio = result["metrics"]["diversification"]["diversification_ratio"]
        eff_n = result["metrics"]["diversification"]["effective_number_of_assets"]
        details = f"Div Ratio: {div_ratio:.2f}, Effective Assets: {eff_n:.2f}"
    else:
        details = result.get("error", "Unknown error")

    print_result("Diversified Portfolio", success, details)
    results.append(success)

    # Test 3: Concentration risk
    print(f"\n{Colors.BLUE}Test 3: Concentrated portfolio (top-heavy){Colors.RESET}")
    result = await tool.execute({
        "portfolio": [
            {"symbol": "AAPL", "weight": 0.50},
            {"symbol": "MSFT", "weight": 0.30},
            {"symbol": "GOOGL", "weight": 0.20}
        ]
    })

    success = "error" not in result and "concentration" in result.get("metrics", {})
    if success:
        top3 = result["metrics"]["concentration"]["top3_concentration_percent"]
        hhi = result["metrics"]["concentration"]["herfindahl_index"]
        details = f"Top3: {top3:.0f}%, HHI: {hhi:.4f}"
    else:
        details = result.get("error", "Unknown error")

    print_result("Concentration Analysis", success, details)
    results.append(success)

    # Test 4: Portfolio VaR
    print(f"\n{Colors.BLUE}Test 4: Portfolio VaR calculation{Colors.RESET}")
    result = await tool.execute({
        "portfolio": [
            {"symbol": "AAPL", "weight": 0.4},
            {"symbol": "MSFT", "weight": 0.3},
            {"symbol": "GOOGL", "weight": 0.3}
        ],
        "confidence_level": 0.99
    })

    success = "error" not in result and "var" in result.get("metrics", {})
    if success:
        hist_var = result["metrics"]["var"]["historical_var_percent"]
        cvar = result["metrics"]["var"]["historical_cvar_percent"]
        details = f"99% VaR: {hist_var:.2f}%, CVaR: {cvar:.2f}%"
    else:
        details = result.get("error", "Unknown error")

    print_result("Portfolio VaR", success, details)
    results.append(success)

    return results


async def main():
    """Run all tests"""
    print(f"{Colors.BOLD}{Colors.MAGENTA}")
    print("="*80)
    print(" Risk Spoke Test Suite ".center(80))
    print("="*80)
    print(Colors.RESET)

    all_results = []

    # Test VaR Calculator
    var_results = await test_var_calculator()
    all_results.extend(var_results)

    # Test Risk Metrics
    metrics_results = await test_risk_metrics()
    all_results.extend(metrics_results)

    # Test Portfolio Risk
    portfolio_results = await test_portfolio_risk()
    all_results.extend(portfolio_results)

    # Summary
    print_header("Test Summary")

    total = len(all_results)
    passed = sum(all_results)
    failed = total - passed

    print(f"{Colors.BOLD}Total Tests: {total}{Colors.RESET}")
    print(f"{Colors.GREEN}Passed: {passed}{Colors.RESET}")
    if failed > 0:
        print(f"{Colors.RED}Failed: {failed}{Colors.RESET}")

    success_rate = (passed / total * 100) if total > 0 else 0
    print(f"\n{Colors.BOLD}Success Rate: {success_rate:.1f}%{Colors.RESET}")

    if success_rate == 100:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 All tests passed!{Colors.RESET}")
    elif success_rate >= 80:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️  Most tests passed{Colors.RESET}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ Many tests failed{Colors.RESET}")

    print()
    return 0 if success_rate == 100 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
