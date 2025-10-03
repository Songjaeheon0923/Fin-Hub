"""
Test New Portfolio Tools (Week 3-4)

Tests for performance_analyzer, backtester, and factor_analyzer.
"""

import asyncio
import sys
from pathlib import Path
import logging

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir / "app"))

from tools.performance_analyzer import performance_analyzer
from tools.backtester import backtester
from tools.factor_analyzer import factor_analyzer

# Configure logging
logging.basicConfig(
    level=logging.WARNING,  # Reduce noise
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_test_header(test_name: str):
    """Print test header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}TEST: {test_name}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")


def print_result(success: bool, message: str = ""):
    """Print test result"""
    if success:
        print(f"{Colors.GREEN}[PASS]{Colors.END} {message}")
    else:
        print(f"{Colors.RED}[FAIL]{Colors.END} {message}")


async def test_performance_analyzer():
    """
    Test 1: Performance Analyzer
    """
    print_test_header("Performance Analyzer")

    try:
        # Sample positions
        positions = {
            "AAPL": {"shares": 100, "avg_cost": 150, "current_price": 185},
            "MSFT": {"shares": 50, "avg_cost": 300, "current_price": 420}
        }

        result = await performance_analyzer(
            positions=positions,
            benchmark="SPY",
            start_date="2024-01-01"
        )

        # Validate result
        assert "returns" in result, "Missing 'returns'"
        assert "risk_metrics" in result, "Missing 'risk_metrics'"
        assert "benchmark_comparison" in result, "Missing 'benchmark_comparison'"
        assert "attribution" in result, "Missing 'attribution'"

        print(f"Total Return: {result['returns']['total_return']:.2%}")
        print(f"Sharpe Ratio: {result['risk_metrics']['sharpe_ratio']:.2f}")
        print(f"Max Drawdown: {result['risk_metrics']['max_drawdown']:.2%}")

        print_result(True, "Performance analyzer test successful")
        return True

    except Exception as e:
        print_result(False, f"Error: {str(e)}")
        return False


async def test_backtester():
    """
    Test 2: Backtester
    """
    print_test_header("Backtester - Momentum Strategy")

    try:
        result = await backtester(
            strategy="momentum",
            universe="sp500",
            start_date="2024-01-01",
            end_date="2024-06-01",
            initial_capital=100000,
            rebalance_frequency="monthly",
            parameters={"lookback": 60, "top_n": 10}
        )

        # Validate result
        assert "performance" in result, "Missing 'performance'"
        assert "equity_curve" in result, "Missing 'equity_curve'"
        assert "trades" in result, "Missing 'trades'"

        print(f"Total Return: {result['performance']['total_return']:.2%}")
        print(f"Sharpe Ratio: {result['performance']['sharpe_ratio']:.2f}")
        print(f"Max Drawdown: {result['performance']['max_drawdown']:.2%}")
        print(f"Number of Trades: {result['metadata']['total_trades']}")

        print_result(True, "Backtester test successful")
        return True

    except Exception as e:
        print_result(False, f"Error: {str(e)}")
        return False


async def test_factor_analyzer():
    """
    Test 3: Factor Analyzer
    """
    print_test_header("Factor Analyzer")

    try:
        positions = {
            "AAPL": 0.35,
            "MSFT": 0.40,
            "GOOGL": 0.25
        }

        result = await factor_analyzer(
            positions=positions,
            factors=["market", "size", "value", "momentum"],
            start_date="2024-01-01"
        )

        # Validate result
        assert "factor_exposures" in result, "Missing 'factor_exposures'"
        assert "factor_returns" in result, "Missing 'factor_returns'"
        assert "r_squared" in result, "Missing 'r_squared'"

        print(f"Market Beta: {result['factor_exposures'].get('market', 0):.2f}")
        print(f"R-squared: {result['r_squared']:.2%}")
        print(f"Alpha: {result.get('alpha', 0):.2%}")

        print_result(True, "Factor analyzer test successful")
        return True

    except Exception as e:
        print_result(False, f"Error: {str(e)}")
        return False


async def run_all_tests():
    """
    Run all tests.
    """
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}")
    print(f"Portfolio Spoke - New Tools Test Suite (Week 3-4)")
    print(f"{'='*60}{Colors.END}\n")

    tests = [
        ("Performance Analyzer", test_performance_analyzer),
        ("Backtester", test_backtester),
        ("Factor Analyzer", test_factor_analyzer),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            success = await test_func()
            results.append((test_name, success))
        except Exception as e:
            logger.error(f"Test {test_name} failed with exception: {e}")
            results.append((test_name, False))

    # Summary
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}")
    print(f"Test Summary")
    print(f"{'='*60}{Colors.END}\n")

    total = len(results)
    passed = sum(1 for _, success in results if success)
    failed = total - passed

    for test_name, success in results:
        status = f"{Colors.GREEN}PASS{Colors.END}" if success else f"{Colors.RED}FAIL{Colors.END}"
        print(f"  {status} - {test_name}")

    print(f"\n{Colors.BOLD}Total: {total}, Passed: {Colors.GREEN}{passed}{Colors.END}, "
          f"Failed: {Colors.RED}{failed}{Colors.END}{Colors.BOLD}")

    success_rate = (passed / total * 100) if total > 0 else 0
    print(f"Success Rate: {success_rate:.1f}%{Colors.END}\n")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
