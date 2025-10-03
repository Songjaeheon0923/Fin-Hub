#!/usr/bin/env python3
"""
Complete Risk Spoke Test Suite
Tests all 8 risk management tools
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
from app.tools.stress_testing import StressTestingTool
from app.tools.tail_risk import TailRiskTool
from app.tools.greeks_calculator import GreeksCalculatorTool
from app.tools.compliance_checker import ComplianceCheckerTool
from app.tools.risk_dashboard import RiskDashboardTool


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
    """Test VaR Calculator Tool (3 tests)"""
    print_header("1. VaR Calculator")

    tool = VaRCalculatorTool()
    results = []

    # Test 1: Historical VaR
    print(f"{Colors.BLUE}Test 1.1: Historical VaR for AAPL{Colors.RESET}")
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
    print(f"\n{Colors.BLUE}Test 1.2: All VaR methods for TSLA{Colors.RESET}")
    result = await tool.execute({
        "symbol": "TSLA",
        "method": "all",
        "confidence_level": 0.99
    })

    success = "error" not in result and len(result.get("methods", {})) == 3
    if success:
        methods = ", ".join(result["methods"].keys())
        details = f"Calculated: {methods}"
    else:
        details = result.get("error", "Unknown error")

    print_result("All VaR Methods", success, details)
    results.append(success)

    # Test 3: CVaR
    print(f"\n{Colors.BLUE}Test 1.3: CVaR calculation{Colors.RESET}")
    result = await tool.execute({
        "symbol": "NVDA",
        "method": "historical",
        "confidence_level": 0.95
    })

    success = "error" not in result and "cvar_usd" in result.get("methods", {}).get("historical", {})
    if success:
        cvar = result["methods"]["historical"]["cvar_usd"]
        details = f"CVaR: ${cvar:,.2f}"
    else:
        details = result.get("error", "Unknown error")

    print_result("CVaR Calculation", success, details)
    results.append(success)

    return results


async def test_stress_testing():
    """Test Stress Testing Tool (3 tests)"""
    print_header("2. Stress Testing")

    tool = StressTestingTool()
    results = []

    # Test 1: Historical crisis
    print(f"{Colors.BLUE}Test 2.1: 2008 Financial Crisis scenario{Colors.RESET}")
    result = await tool.execute({
        "symbol": "AAPL",
        "scenarios": ["2008_financial_crisis"],
        "portfolio_value": 100000
    })

    success = "error" not in result and "2008_financial_crisis" in result.get("scenarios", {})
    if success:
        scenario = result["scenarios"]["2008_financial_crisis"]
        loss_pct = scenario.get("loss_percent", 0)
        details = f"Loss: {loss_pct:.2f}%"
    else:
        details = result.get("error", "Unknown error")

    print_result("2008 Crisis Stress Test", success, details)
    results.append(success)

    # Test 2: Multiple scenarios
    print(f"\n{Colors.BLUE}Test 2.2: Multiple stress scenarios{Colors.RESET}")
    result = await tool.execute({
        "symbol": "TSLA",
        "scenarios": ["2020_covid_crash", "2022_inflation_shock"]
    })

    success = "error" not in result and len(result.get("scenarios", {})) == 2
    if success:
        scenarios = list(result["scenarios"].keys())
        details = f"Scenarios: {', '.join(scenarios)}"
    else:
        details = result.get("error", "Unknown error")

    print_result("Multiple Scenarios", success, details)
    results.append(success)

    # Test 3: Worst case
    print(f"\n{Colors.BLUE}Test 2.3: Worst case identification{Colors.RESET}")
    result = await tool.execute({
        "symbol": "MSFT",
        "scenarios": ["2008_financial_crisis", "2020_covid_crash"]
    })

    success = "error" not in result and "worst_case_scenario" in result
    if success:
        worst = result["worst_case_scenario"].get("scenario_name", "Unknown")
        details = f"Worst: {worst}"
    else:
        details = result.get("error", "Unknown error")

    print_result("Worst Case Detection", success, details)
    results.append(success)

    return results


async def test_tail_risk():
    """Test Tail Risk Analyzer (3 tests)"""
    print_header("3. Tail Risk Analyzer")

    tool = TailRiskTool()
    results = []

    # Test 1: EVT analysis
    print(f"{Colors.BLUE}Test 3.1: Extreme Value Theory{Colors.RESET}")
    result = await tool.execute({
        "symbol": "AAPL",
        "analysis": ["extreme_value"]
    })

    success = "error" not in result and "extreme_value_theory" in result.get("analyses", {})
    if success:
        evt = result["analyses"]["extreme_value_theory"]
        shape = evt.get("parameters", {}).get("shape_xi", 0)
        details = f"Shape parameter (ξ): {shape:.4f}"
    else:
        details = result.get("error", "Unknown error")

    print_result("EVT Analysis", success, details)
    results.append(success)

    # Test 2: Fat tail analysis
    print(f"\n{Colors.BLUE}Test 3.2: Fat Tail Analysis{Colors.RESET}")
    result = await tool.execute({
        "symbol": "TSLA",
        "analysis": ["fat_tail"]
    })

    success = "error" not in result and "fat_tail" in result.get("analyses", {})
    if success:
        ratio = result["analyses"]["fat_tail"].get("fat_tail_ratio", 0)
        details = f"Fat tail ratio: {ratio:.3f}"
    else:
        details = result.get("error", "Unknown error")

    print_result("Fat Tail Analysis", success, details)
    results.append(success)

    # Test 3: Black swan
    print(f"\n{Colors.BLUE}Test 3.3: Black Swan Analysis{Colors.RESET}")
    result = await tool.execute({
        "symbol": "NVDA",
        "analysis": ["black_swan"]
    })

    success = "error" not in result and "black_swan" in result.get("analyses", {})
    if success:
        bs = result["analyses"]["black_swan"]
        events_5 = bs.get("extreme_event_frequencies", {}).get("5_sigma_events", {}).get("actual", 0)
        details = f"5σ events: {events_5}"
    else:
        details = result.get("error", "Unknown error")

    print_result("Black Swan Analysis", success, details)
    results.append(success)

    return results


async def test_greeks_calculator():
    """Test Greeks Calculator (3 tests)"""
    print_header("4. Greeks Calculator")

    tool = GreeksCalculatorTool()
    results = []

    # Test 1: Call Greeks
    print(f"{Colors.BLUE}Test 4.1: Call option Greeks{Colors.RESET}")
    result = await tool.execute({
        "symbol": "AAPL",
        "option_type": "call",
        "time_to_expiry": 30,
        "greeks": ["delta", "gamma", "vega"]
    })

    success = "error" not in result and "call" in result
    if success:
        delta = result["call"]["delta"]["value"]
        details = f"Call Delta: {delta:.4f}"
    else:
        details = result.get("error", "Unknown error")

    print_result("Call Greeks", success, details)
    results.append(success)

    # Test 2: Put Greeks
    print(f"\n{Colors.BLUE}Test 4.2: Put option Greeks{Colors.RESET}")
    result = await tool.execute({
        "symbol": "TSLA",
        "option_type": "put",
        "greeks": ["delta", "theta"]
    })

    success = "error" not in result and "put" in result
    if success:
        theta = result["put"]["theta"]["value"]
        details = f"Put Theta: ${theta:.4f}/day"
    else:
        details = result.get("error", "Unknown error")

    print_result("Put Greeks", success, details)
    results.append(success)

    # Test 3: Both types
    print(f"\n{Colors.BLUE}Test 4.3: Both call and put Greeks{Colors.RESET}")
    result = await tool.execute({
        "symbol": "MSFT",
        "option_type": "both",
        "greeks": ["all"]
    })

    success = "error" not in result and "call" in result and "put" in result
    if success:
        call_greeks = len([k for k in result["call"].keys() if k not in ["price", "intrinsic_value", "time_value"]])
        details = f"Greeks calculated: {call_greeks} per option"
    else:
        details = result.get("error", "Unknown error")

    print_result("Both Option Types", success, details)
    results.append(success)

    return results


async def test_compliance_checker():
    """Test Compliance Checker (3 tests)"""
    print_header("5. Compliance Checker")

    tool = ComplianceCheckerTool()
    results = []

    # Test 1: Entity screening
    print(f"{Colors.BLUE}Test 5.1: Entity screening{Colors.RESET}")
    result = await tool.execute({
        "check_type": "entity_screening",
        "entity_name": "Test Corporation",
        "jurisdiction": "US"
    })

    success = "error" not in result and "entity_screening" in result
    if success:
        risk = result["entity_screening"].get("risk_level", "UNKNOWN")
        details = f"Risk level: {risk}"
    else:
        details = result.get("error", "Unknown error")

    print_result("Entity Screening", success, details)
    results.append(success)

    # Test 2: Trading pattern analysis
    print(f"\n{Colors.BLUE}Test 5.2: Trading pattern monitoring{Colors.RESET}")
    result = await tool.execute({
        "check_type": "transaction_monitoring",
        "symbol": "AAPL",
        "period": 90
    })

    success = "error" not in result and "transaction_monitoring" in result
    if success:
        risk = result["transaction_monitoring"].get("risk_level", "UNKNOWN")
        details = f"Trading risk: {risk}"
    else:
        details = result.get("error", "Unknown error")

    print_result("Trading Patterns", success, details)
    results.append(success)

    # Test 3: Regulatory compliance
    print(f"\n{Colors.BLUE}Test 5.3: Regulatory compliance check{Colors.RESET}")
    result = await tool.execute({
        "check_type": "regulatory_compliance",
        "entity_type": "organization",
        "jurisdiction": "US"
    })

    success = "error" not in result and "regulatory_compliance" in result
    if success:
        regs = result["regulatory_compliance"].get("applicable_regulations", 0)
        details = f"Applicable regulations: {regs}"
    else:
        details = result.get("error", "Unknown error")

    print_result("Regulatory Compliance", success, details)
    results.append(success)

    return results


async def test_risk_dashboard():
    """Test Risk Dashboard (2 tests)"""
    print_header("6. Risk Dashboard")

    tool = RiskDashboardTool()
    results = []

    # Test 1: Single asset dashboard
    print(f"{Colors.BLUE}Test 6.1: Single asset dashboard{Colors.RESET}")
    result = await tool.execute({
        "analysis_type": "single_asset",
        "symbol": "AAPL",
        "portfolio_value": 100000,
        "include_stress_test": True,
        "include_tail_risk": True
    })

    success = "error" not in result and "overall_assessment" in result
    if success:
        risk_score = result["overall_assessment"].get("overall_risk_score", 0)
        details = f"Risk score: {risk_score:.2f}/100"
    else:
        details = result.get("error", "Unknown error")

    print_result("Single Asset Dashboard", success, details)
    results.append(success)

    # Test 2: Portfolio dashboard
    print(f"\n{Colors.BLUE}Test 6.2: Portfolio dashboard{Colors.RESET}")
    result = await tool.execute({
        "analysis_type": "portfolio",
        "portfolio": [
            {"symbol": "AAPL", "weight": 0.4},
            {"symbol": "MSFT", "weight": 0.3},
            {"symbol": "GOOGL", "weight": 0.3}
        ],
        "portfolio_value": 100000
    })

    success = "error" not in result and "portfolio_metrics" in result
    if success:
        sharpe = result["portfolio_metrics"]["performance"].get("sharpe_ratio", 0)
        details = f"Portfolio Sharpe: {sharpe:.2f}"
    else:
        details = result.get("error", "Unknown error")

    print_result("Portfolio Dashboard", success, details)
    results.append(success)

    return results


async def main():
    """Run all tests"""
    print(f"{Colors.BOLD}{Colors.MAGENTA}")
    print("="*80)
    print(" Complete Risk Spoke Test Suite - 8 Tools ".center(80))
    print("="*80)
    print(Colors.RESET)

    all_results = []

    # Test all 8 tools
    var_results = await test_var_calculator()
    all_results.extend(var_results)

    # Note: Skip Risk Metrics and Portfolio Risk tests as they were tested in the original suite

    stress_results = await test_stress_testing()
    all_results.extend(stress_results)

    tail_results = await test_tail_risk()
    all_results.extend(tail_results)

    greeks_results = await test_greeks_calculator()
    all_results.extend(greeks_results)

    compliance_results = await test_compliance_checker()
    all_results.extend(compliance_results)

    dashboard_results = await test_risk_dashboard()
    all_results.extend(dashboard_results)

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
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 All new tools passing!{Colors.RESET}")
    elif success_rate >= 80:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️  Most tests passed{Colors.RESET}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ Many tests failed{Colors.RESET}")

    print()
    return 0 if success_rate == 100 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
