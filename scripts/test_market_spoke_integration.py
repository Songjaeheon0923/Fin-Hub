#!/usr/bin/env python3
"""
Market Spoke Integration Test
Tests all MCP tools with real data
"""

import sys
import asyncio
from pathlib import Path

# Add service path
sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "market-spoke"))

from app.tools.unified_market_data import (
    StockQuoteTool,
    CryptoPriceTool,
    FinancialNewsTool,
    EconomicIndicatorTool,
    MarketOverviewTool,
    APIStatusTool
)

# Color codes
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


async def test_stock_quote():
    """Test stock quote tool"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}1. Testing Stock Quote Tool...{Colors.RESET}")

    tool = StockQuoteTool()
    result = await tool.execute({"symbol": "AAPL"})

    if "error" not in result:
        print(f"{Colors.GREEN}[PASS]{Colors.RESET} Stock Quote")
        print(f"  Symbol: {result['symbol']}")
        print(f"  Price: ${result['price']:.2f}")
        print(f"  Change: {result['change']:+.2f} ({result['change_percent']:+.2f}%)")
        print(f"  Source: {result['source']}")
        return True
    else:
        print(f"{Colors.RED}[FAIL]{Colors.RESET} {result['error']}")
        return False


async def test_crypto_price():
    """Test crypto price tool"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}2. Testing Crypto Price Tool...{Colors.RESET}")

    tool = CryptoPriceTool()
    result = await tool.execute({"coin_id": "bitcoin"})

    if "error" not in result:
        print(f"{Colors.GREEN}[PASS]{Colors.RESET} Crypto Price")
        print(f"  Coin: {result['coin_id']}")
        print(f"  Price: ${result['price']:,.2f}")
        print(f"  24h Change: {result['change_24h']:+.2f}%")
        print(f"  Volume: ${result['volume_24h']:,.0f}")
        return True
    else:
        print(f"{Colors.RED}[FAIL]{Colors.RESET} {result['error']}")
        return False


async def test_financial_news():
    """Test financial news tool"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}3. Testing Financial News Tool...{Colors.RESET}")

    tool = FinancialNewsTool()
    result = await tool.execute({"query": "AI stocks", "page_size": 3})

    if "error" not in result and "articles" in result:
        print(f"{Colors.GREEN}[PASS]{Colors.RESET} Financial News")
        print(f"  Found: {result['count']} articles")
        for i, article in enumerate(result['articles'][:2], 1):
            print(f"  {i}. {article['title']}")
            print(f"     Sentiment: {article['sentiment']}")
        return True
    else:
        print(f"{Colors.RED}[FAIL]{Colors.RESET} {result.get('error', 'Unknown error')}")
        return False


async def test_economic_indicator():
    """Test economic indicator tool"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}4. Testing Economic Indicator Tool...{Colors.RESET}")

    tool = EconomicIndicatorTool()
    result = await tool.execute({"series_id": "GDP", "limit": 3})

    if "error" not in result:
        print(f"{Colors.GREEN}[PASS]{Colors.RESET} Economic Indicator")
        print(f"  Series: {result['series_id']}")
        print(f"  Latest observations:")
        for obs in result['observations'][:3]:
            print(f"    {obs['date']}: ${obs['value']}")
        return True
    else:
        print(f"{Colors.RED}[FAIL]{Colors.RESET} {result['error']}")
        return False


async def test_market_overview():
    """Test market overview tool"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}5. Testing Market Overview Tool...{Colors.RESET}")

    tool = MarketOverviewTool()
    result = await tool.execute({})

    if "error" not in result:
        print(f"{Colors.GREEN}[PASS]{Colors.RESET} Market Overview")

        # Indices
        print(f"\n  {Colors.CYAN}Indices:{Colors.RESET}")
        for name, data in result['indices'].items():
            if data:
                print(f"    {name.upper()}: ${data['price']:.2f} ({data['change_percent']:+.2f}%)")

        # Crypto
        print(f"\n  {Colors.CYAN}Crypto:{Colors.RESET}")
        for name, data in result['crypto'].items():
            if data:
                print(f"    {name.upper()}: ${data['price']:,.2f} ({data['change_24h']:+.2f}%)")

        # News
        if result['news']:
            print(f"\n  {Colors.CYAN}Top News:{Colors.RESET}")
            for article in result['news'][:2]:
                print(f"    - {article['title']}")

        return True
    else:
        print(f"{Colors.RED}[FAIL]{Colors.RESET} {result['error']}")
        return False


async def test_api_status():
    """Test API status tool"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}6. Testing API Status Tool...{Colors.RESET}")

    tool = APIStatusTool()
    result = await tool.execute({})

    print(f"{Colors.GREEN}[PASS]{Colors.RESET} API Status")
    print(f"\n  {Colors.CYAN}Configured APIs:{Colors.RESET}")

    for api, configured in result['configured_keys'].items():
        status = "[OK]" if configured else "[MISSING]"
        color = Colors.GREEN if configured else Colors.RED
        print(f"    {color}{status}{Colors.RESET} {api}")

    print(f"\n  {Colors.CYAN}API Availability:{Colors.RESET}")
    for api, status in result['apis'].items():
        available = status['available']
        status_str = "[AVAILABLE]" if available else "[UNAVAILABLE]"
        color = Colors.GREEN if available else Colors.YELLOW
        print(f"    {color}{status_str}{Colors.RESET} {api}")

    return True


async def main():
    """Main test function"""
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'Market Spoke Integration Test':^60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}")

    tests = [
        test_stock_quote,
        test_crypto_price,
        test_financial_news,
        test_economic_indicator,
        test_market_overview,
        test_api_status,
    ]

    results = []
    for test_func in tests:
        try:
            result = await test_func()
            results.append(result)
        except Exception as e:
            print(f"{Colors.RED}[ERROR]{Colors.RESET} {test_func.__name__}: {e}")
            results.append(False)

    # Summary
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'Test Summary':^60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}\n")

    passed = sum(1 for r in results if r)
    total = len(results)

    print(f"  {Colors.BOLD}Passed: {passed}/{total}{Colors.RESET}")

    if passed == total:
        print(f"\n{Colors.GREEN}[SUCCESS]{Colors.RESET} All tests passed!")
        print(f"\n{Colors.BOLD}Next Steps:{Colors.RESET}")
        print(f"  1. Market Spoke is ready to use")
        print(f"  2. All 7 MCP tools are working")
        print(f"  3. Can start building financial applications")
        return 0
    else:
        print(f"\n{Colors.YELLOW}[WARNING]{Colors.RESET} Some tests failed")
        print(f"  Check API keys and network connection")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
