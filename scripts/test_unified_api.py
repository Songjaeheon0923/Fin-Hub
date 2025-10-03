#!/usr/bin/env python3
"""
Test Unified API Manager
Verifies all API integrations work correctly
"""

import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "market-spoke"))

from app.clients.unified_api_manager import UnifiedAPIManager

# Color codes
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


async def test_stock_quote():
    """Test stock quote API"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}Testing Stock Quote...{Colors.RESET}")

    async with UnifiedAPIManager() as api:
        quote = await api.get_stock_quote("AAPL")

        if quote:
            print(f"{Colors.GREEN}[OK] AAPL: ${quote['price']:.2f}{Colors.RESET}")
            print(f"  Change: {quote['change']:+.2f} ({quote['change_percent']:+.2f}%)")
            print(f"  High: ${quote['high']:.2f}, Low: ${quote['low']:.2f}")
            print(f"  Source: {quote['source']}")
            return True
        else:
            print(f"{Colors.RED}[ERROR] Failed to get stock quote{Colors.RESET}")
            return False


async def test_crypto_price():
    """Test cryptocurrency price API"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}Testing Crypto Price...{Colors.RESET}")

    async with UnifiedAPIManager() as api:
        btc = await api.get_crypto_price("bitcoin")

        if btc:
            print(f"{Colors.GREEN}[OK] Bitcoin: ${btc['price']:,.2f}{Colors.RESET}")
            print(f"  24h Change: {btc['change_24h']:+.2f}%")
            print(f"  24h Volume: ${btc['volume_24h']:,.0f}")
            print(f"  Market Cap: ${btc['market_cap']:,.0f}")
            return True
        else:
            print(f"{Colors.RED}[ERROR] Failed to get crypto price{Colors.RESET}")
            return False


async def test_financial_news():
    """Test financial news API"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}Testing Financial News...{Colors.RESET}")

    async with UnifiedAPIManager() as api:
        news = await api.get_financial_news("tech stocks", page_size=5)

        if news:
            print(f"{Colors.GREEN}[OK] Found {len(news)} articles{Colors.RESET}")
            for article in news[:3]:
                print(f"\n  Title: {article['title']}")
                print(f"  Source: {article['source']}")
                print(f"  Sentiment: {article['sentiment']}")
            return True
        else:
            print(f"{Colors.RED}[ERROR] Failed to get news{Colors.RESET}")
            return False


async def test_economic_indicator():
    """Test economic indicator API"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}Testing Economic Indicator...{Colors.RESET}")

    async with UnifiedAPIManager() as api:
        gdp = await api.get_economic_indicator("GDP", limit=5)

        if gdp:
            print(f"{Colors.GREEN}[OK] GDP Data (Latest 5):{Colors.RESET}")
            for obs in gdp['observations'][:3]:
                print(f"  {obs['date']}: ${obs['value']}")
            return True
        else:
            print(f"{Colors.RED}[ERROR] Failed to get economic data{Colors.RESET}")
            return False


async def test_sanctions_check():
    """Test sanctions check API"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}Testing Sanctions Check...{Colors.RESET}")

    async with UnifiedAPIManager() as api:
        result = await api.check_sanctions("Vladimir Putin")

        if result:
            print(f"{Colors.GREEN}[OK] Sanctions Check:{Colors.RESET}")
            print(f"  Query: {result['query']}")
            print(f"  Total Results: {result['total_results']}")
            print(f"  Top Matches: {len(result['results'])}")
            return True
        else:
            print(f"{Colors.RED}[ERROR] Failed to check sanctions{Colors.RESET}")
            return False


async def test_batch_quotes():
    """Test batch quote retrieval"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}Testing Batch Quotes...{Colors.RESET}")

    symbols = ["AAPL", "GOOGL", "MSFT", "TSLA"]

    async with UnifiedAPIManager() as api:
        quotes = await api.get_multiple_quotes(symbols)

        success_count = sum(1 for q in quotes.values() if q is not None)

        if success_count > 0:
            print(f"{Colors.GREEN}[OK] Retrieved {success_count}/{len(symbols)} quotes{Colors.RESET}")
            for symbol, quote in quotes.items():
                if quote:
                    print(f"  {symbol}: ${quote['price']:.2f} ({quote['change_percent']:+.2f}%)")
            return True
        else:
            print(f"{Colors.RED}[ERROR] Failed to get batch quotes{Colors.RESET}")
            return False


async def test_market_overview():
    """Test comprehensive market overview"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}Testing Market Overview...{Colors.RESET}")

    async with UnifiedAPIManager() as api:
        overview = await api.get_market_overview()

        if overview:
            print(f"{Colors.GREEN}[OK] Market Overview Retrieved{Colors.RESET}")

            # Indices
            print(f"\n  {Colors.CYAN}Indices:{Colors.RESET}")
            for name, data in overview['indices'].items():
                if data:
                    print(f"    {name.upper()}: ${data['price']:.2f} ({data['change_percent']:+.2f}%)")

            # Crypto
            print(f"\n  {Colors.CYAN}Crypto:{Colors.RESET}")
            for name, data in overview['crypto'].items():
                if data:
                    print(f"    {name.upper()}: ${data['price']:,.2f} ({data['change_24h']:+.2f}%)")

            # News
            if overview['news']:
                print(f"\n  {Colors.CYAN}Latest News:{Colors.RESET}")
                for article in overview['news'][:2]:
                    print(f"    - {article['title']}")

            return True
        else:
            print(f"{Colors.RED}[ERROR] Failed to get market overview{Colors.RESET}")
            return False


async def test_api_status():
    """Test API status checking"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}Testing API Status...{Colors.RESET}")

    async with UnifiedAPIManager() as api:
        # Trigger some API calls first
        await api.get_stock_quote("AAPL")

        status = api.get_api_status()

        print(f"{Colors.GREEN}[OK] API Status:{Colors.RESET}")
        print(f"\n  {Colors.CYAN}Configured Keys:{Colors.RESET}")
        for api_name, is_configured in status['configured_keys'].items():
            status_str = "[OK]" if is_configured else "[MISSING]"
            color = Colors.GREEN if is_configured else Colors.RED
            print(f"    {color}{status_str}{Colors.RESET} {api_name}")

        print(f"\n  {Colors.CYAN}API Availability:{Colors.RESET}")
        for api_name, api_status in status['apis'].items():
            status_str = "[AVAILABLE]" if api_status['available'] else "[UNAVAILABLE]"
            color = Colors.GREEN if api_status['available'] else Colors.YELLOW
            print(f"    {color}{status_str}{Colors.RESET} {api_name}")

        return True


async def main():
    """Main test function"""
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'Unified API Manager Test Suite':^60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}")

    tests = [
        ("Stock Quote", test_stock_quote),
        ("Crypto Price", test_crypto_price),
        ("Financial News", test_financial_news),
        ("Economic Indicator", test_economic_indicator),
        ("Sanctions Check", test_sanctions_check),
        ("Batch Quotes", test_batch_quotes),
        ("Market Overview", test_market_overview),
        ("API Status", test_api_status),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"{Colors.RED}[ERROR] {test_name} failed: {e}{Colors.RESET}")
            results.append((test_name, False))

    # Summary
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'Test Summary':^60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}\n")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status_str = "[PASS]" if result else "[FAIL]"
        color = Colors.GREEN if result else Colors.RED
        print(f"  {color}{status_str}{Colors.RESET} {test_name}")

    print(f"\n{Colors.BOLD}Results: {passed}/{total} tests passed{Colors.RESET}")

    if passed == total:
        print(f"{Colors.GREEN}[OK] All tests passed!{Colors.RESET}")
        return 0
    else:
        print(f"{Colors.YELLOW}[WARN] Some tests failed{Colors.RESET}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
