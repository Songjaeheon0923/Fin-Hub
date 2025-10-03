"""
Test Portfolio Spoke Tools

Tests for portfolio optimization and rebalancing tools.
"""

import asyncio
import sys
from pathlib import Path
import logging

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir / "app"))

from tools.portfolio_optimizer import portfolio_optimizer
from tools.portfolio_rebalancer import portfolio_rebalancer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
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


async def test_portfolio_optimizer_max_sharpe():
    """
    Test 1: Portfolio Optimizer - Max Sharpe Ratio
    """
    print_test_header("Portfolio Optimizer - Max Sharpe Ratio")

    try:
        result = await portfolio_optimizer(
            tickers=["AAPL", "MSFT", "GOOGL", "AMZN"],
            method="mean_variance",
            objective="max_sharpe",
            risk_free_rate=0.03
        )

        # Validate result
        assert "weights" in result, "Missing 'weights' in result"
        assert "expected_return" in result, "Missing 'expected_return'"
        assert "sharpe_ratio" in result, "Missing 'sharpe_ratio'"

        # Check weights sum to 1
        total_weight = sum(result["weights"].values())
        assert abs(total_weight - 1.0) < 0.01, f"Weights sum to {total_weight}, expected 1.0"

        # Check Sharpe ratio is positive
        assert result["sharpe_ratio"] > 0, "Sharpe ratio should be positive"

        print(f"Weights: {result['weights']}")
        print(f"Expected Return: {result['expected_return']:.2%}")
        print(f"Expected Risk: {result['expected_risk']:.2%}")
        print(f"Sharpe Ratio: {result['sharpe_ratio']:.2f}")

        print_result(True, "Max Sharpe optimization successful")
        return True

    except Exception as e:
        print_result(False, f"Error: {str(e)}")
        return False


async def test_portfolio_optimizer_min_volatility():
    """
    Test 2: Portfolio Optimizer - Min Volatility
    """
    print_test_header("Portfolio Optimizer - Min Volatility")

    try:
        result = await portfolio_optimizer(
            tickers=["AAPL", "MSFT", "GOOGL"],
            method="mean_variance",
            objective="min_volatility"
        )

        assert "weights" in result
        assert "expected_risk" in result

        print(f"Weights: {result['weights']}")
        print(f"Expected Risk: {result['expected_risk']:.2%}")

        print_result(True, "Min volatility optimization successful")
        return True

    except Exception as e:
        print_result(False, f"Error: {str(e)}")
        return False


async def test_portfolio_optimizer_hrp():
    """
    Test 3: Portfolio Optimizer - HRP
    """
    print_test_header("Portfolio Optimizer - Hierarchical Risk Parity")

    try:
        result = await portfolio_optimizer(
            tickers=["AAPL", "MSFT", "GOOGL", "JPM", "JNJ"],
            method="hrp"
        )

        assert "weights" in result
        assert result["method_used"] == "hrp"

        print(f"Weights: {result['weights']}")
        print(f"Sharpe Ratio: {result['sharpe_ratio']:.2f}")

        print_result(True, "HRP optimization successful")
        return True

    except Exception as e:
        print_result(False, f"Error: {str(e)}")
        return False


async def test_portfolio_optimizer_risk_parity():
    """
    Test 4: Portfolio Optimizer - Risk Parity
    """
    print_test_header("Portfolio Optimizer - Risk Parity")

    try:
        result = await portfolio_optimizer(
            tickers=["AAPL", "MSFT", "GOOGL"],
            method="risk_parity"
        )

        assert "weights" in result
        assert result["method_used"] == "risk_parity"

        print(f"Weights: {result['weights']}")
        print(f"HHI: {result['metadata']['hhi']:.3f}")

        print_result(True, "Risk Parity optimization successful")
        return True

    except Exception as e:
        print_result(False, f"Error: {str(e)}")
        return False


async def test_portfolio_rebalancer_threshold():
    """
    Test 5: Portfolio Rebalancer - Threshold Strategy
    """
    print_test_header("Portfolio Rebalancer - Threshold Strategy")

    try:
        # Current portfolio (overweight AAPL, underweight MSFT)
        current_positions = {
            "AAPL": {"shares": 120, "value": 22200, "price": 185.00},
            "MSFT": {"shares": 30, "value": 12600, "price": 420.00},
            "GOOGL": {"shares": 40, "value": 6000, "price": 150.00}
        }

        # Target: 30% AAPL, 40% MSFT, 30% GOOGL
        target_weights = {
            "AAPL": 0.30,
            "MSFT": 0.40,
            "GOOGL": 0.30
        }

        result = await portfolio_rebalancer(
            current_positions=current_positions,
            target_weights=target_weights,
            total_value=45000,
            cash_available=5000,
            strategy="threshold",
            threshold=0.05
        )

        assert "rebalancing_needed" in result
        assert "trades" in result

        print(f"Rebalancing needed: {result['rebalancing_needed']}")

        if result["rebalancing_needed"]:
            print(f"Number of trades: {len(result['trades'])}")
            print(f"Total cost: ${result['total_cost']:.2f}")
            print(f"Turnover: {result['turnover']:.1%}")

            print("\nTrades:")
            for trade in result["trades"]:
                print(f"  {trade['action'].upper()} {trade['shares']} {trade['ticker']} "
                      f"@ ${trade['price']:.2f} = ${trade['value']:,.2f}")

        print_result(True, "Rebalancer threshold test successful")
        return True

    except Exception as e:
        print_result(False, f"Error: {str(e)}")
        return False


async def test_portfolio_rebalancer_no_rebalance():
    """
    Test 6: Portfolio Rebalancer - No Rebalancing Needed
    """
    print_test_header("Portfolio Rebalancer - No Rebalancing Needed")

    try:
        # Portfolio already at target
        current_positions = {
            "AAPL": {"shares": 100, "value": 30000, "price": 300.00},
            "MSFT": {"shares": 100, "value": 40000, "price": 400.00},
            "GOOGL": {"shares": 200, "value": 30000, "price": 150.00}
        }

        target_weights = {
            "AAPL": 0.30,
            "MSFT": 0.40,
            "GOOGL": 0.30
        }

        result = await portfolio_rebalancer(
            current_positions=current_positions,
            target_weights=target_weights,
            total_value=100000,
            strategy="threshold",
            threshold=0.05
        )

        assert result["rebalancing_needed"] == False, "Should not need rebalancing"

        print(f"Rebalancing needed: {result['rebalancing_needed']}")
        print(f"Reason: {result.get('reason', 'N/A')}")

        print_result(True, "No rebalancing test successful")
        return True

    except Exception as e:
        print_result(False, f"Error: {str(e)}")
        return False


async def run_all_tests():
    """
    Run all tests.
    """
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}")
    print(f"Portfolio Spoke - Test Suite")
    print(f"{'='*60}{Colors.END}\n")

    tests = [
        ("Portfolio Optimizer - Max Sharpe", test_portfolio_optimizer_max_sharpe),
        ("Portfolio Optimizer - Min Volatility", test_portfolio_optimizer_min_volatility),
        ("Portfolio Optimizer - HRP", test_portfolio_optimizer_hrp),
        ("Portfolio Optimizer - Risk Parity", test_portfolio_optimizer_risk_parity),
        ("Portfolio Rebalancer - Threshold", test_portfolio_rebalancer_threshold),
        ("Portfolio Rebalancer - No Rebalance", test_portfolio_rebalancer_no_rebalance),
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
