"""
Test Week 5-6 Portfolio Tools

Tests for asset_allocator, tax_optimizer, and portfolio_dashboard.
"""

import asyncio
import sys
from pathlib import Path
import logging

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir / "app"))

from tools.asset_allocator import asset_allocator
from tools.tax_optimizer import tax_optimizer
from tools.portfolio_dashboard import portfolio_dashboard

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


async def test_asset_allocator():
    """
    Test 1: Asset Allocator
    """
    print_test_header("Asset Allocator")

    try:
        # Sample asset classes
        asset_classes = {
            "US_Equity": ["AAPL", "MSFT", "GOOGL"],
            "Tech": ["NVDA", "AMD"],
            "Healthcare": ["JNJ", "PFE"],
            "Financial": ["JPM", "BAC"]
        }

        # Strategic allocation
        result = await asset_allocator(
            asset_classes=asset_classes,
            allocation_type="strategic",
            risk_tolerance="moderate",
            start_date="2024-01-01"
        )

        # Validate result
        assert "allocation" in result, "Missing 'allocation'"
        assert "asset_weights" in result, "Missing 'asset_weights'"
        assert "diversification" in result, "Missing 'diversification'"
        assert "correlation_analysis" in result, "Missing 'correlation_analysis'"

        # Check allocation sums to 1.0
        total_allocation = sum(result['allocation'].values())
        assert abs(total_allocation - 1.0) < 0.01, f"Allocation sum {total_allocation} != 1.0"

        print(f"Asset Classes: {len(result['allocation'])}")
        print(f"Effective Assets: {result['diversification']['effective_assets']:.2f}")
        print(f"Expected Return: {result['expected_return']:.2%}")
        print(f"Sharpe Ratio: {result['sharpe_ratio']:.2f}")

        print_result(True, "Asset allocator test successful")
        return True

    except Exception as e:
        print_result(False, f"Error: {str(e)}")
        return False


async def test_tax_optimizer():
    """
    Test 2: Tax Optimizer
    """
    print_test_header("Tax Optimizer")

    try:
        # Sample positions
        positions = {
            "AAPL": {
                "shares": 100,
                "cost_basis": 150,
                "current_price": 185,
                "purchase_date": "2023-01-15"
            },
            "TSLA": {
                "shares": 50,
                "cost_basis": 250,
                "current_price": 200,
                "purchase_date": "2024-03-01"
            },
            "MSFT": {
                "shares": 75,
                "cost_basis": 300,
                "current_price": 420,
                "purchase_date": "2022-06-01"
            }
        }

        transactions = [
            {"date": "2024-01-15", "ticker": "AAPL", "shares": 50, "price": 160, "action": "sell"},
            {"date": "2024-01-20", "ticker": "AAPL", "shares": 50, "price": 155, "action": "buy"},
            {"date": "2024-03-01", "ticker": "TSLA", "shares": 50, "price": 250, "action": "buy"}
        ]

        result = await tax_optimizer(
            positions=positions,
            transactions=transactions,
            tax_bracket=0.24,
            ltcg_rate=0.15
        )

        # Validate result
        assert "tax_loss_harvest_opportunities" in result, "Missing 'tax_loss_harvest_opportunities'"
        assert "wash_sale_warnings" in result, "Missing 'wash_sale_warnings'"
        assert "long_term_gains" in result, "Missing 'long_term_gains'"
        assert "short_term_gains" in result, "Missing 'short_term_gains'"

        print(f"TLH Opportunities: {len(result['tax_loss_harvest_opportunities'])}")
        print(f"Wash Sale Warnings: {len(result['wash_sale_warnings'])}")
        print(f"Total Unrealized Gains: ${result['total_unrealized_gains']:.2f}")
        print(f"Potential Tax Savings: ${result['potential_tax_savings']:.2f}")

        print_result(True, "Tax optimizer test successful")
        return True

    except Exception as e:
        print_result(False, f"Error: {str(e)}")
        return False


async def test_portfolio_dashboard():
    """
    Test 3: Portfolio Dashboard
    """
    print_test_header("Portfolio Dashboard")

    try:
        # Sample positions
        positions = {
            "AAPL": {
                "shares": 100,
                "cost_basis": 150,
                "current_price": 185,
                "purchase_date": "2023-01-15"
            },
            "MSFT": {
                "shares": 50,
                "cost_basis": 300,
                "current_price": 420,
                "purchase_date": "2023-06-01"
            },
            "GOOGL": {
                "shares": 80,
                "cost_basis": 120,
                "current_price": 150,
                "purchase_date": "2023-03-01"
            }
        }

        target_weights = {
            "AAPL": 0.33,
            "MSFT": 0.33,
            "GOOGL": 0.34
        }

        result = await portfolio_dashboard(
            positions=positions,
            target_weights=target_weights,
            risk_tolerance="moderate",
            start_date="2024-01-01"
        )

        # Validate result
        assert "health_score" in result, "Missing 'health_score'"
        assert "health_grade" in result, "Missing 'health_grade'"
        assert "performance" in result, "Missing 'performance'"
        assert "risk_assessment" in result, "Missing 'risk_assessment'"
        assert "diversification" in result, "Missing 'diversification'"
        assert "rebalancing" in result, "Missing 'rebalancing'"
        assert "tax_efficiency" in result, "Missing 'tax_efficiency'"

        # Health score should be 0-100
        assert 0 <= result['health_score'] <= 100, f"Invalid health score: {result['health_score']}"

        print(f"Health Score: {result['health_score']}/100 (Grade: {result['health_grade']})")
        print(f"Portfolio Value: ${result['portfolio_value']:,.2f}")
        print(f"Annualized Return: {result['performance']['annualized_return']:.2%}")
        print(f"Sharpe Ratio: {result['performance']['sharpe_ratio']:.2f}")
        print(f"Risk Level: {result['risk_assessment']['risk_level']}")
        print(f"Rebalancing Needed: {result['rebalancing']['needed']}")

        print_result(True, "Portfolio dashboard test successful")
        return True

    except Exception as e:
        print_result(False, f"Error: {str(e)}")
        return False


async def run_all_tests():
    """
    Run all tests.
    """
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}")
    print(f"Portfolio Spoke - Week 5-6 Tools Test Suite")
    print(f"{'='*60}{Colors.END}\n")

    tests = [
        ("Asset Allocator", test_asset_allocator),
        ("Tax Optimizer", test_tax_optimizer),
        ("Portfolio Dashboard", test_portfolio_dashboard),
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
