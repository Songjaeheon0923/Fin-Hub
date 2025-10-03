#!/usr/bin/env python3
"""
Comprehensive API Test Suite for Fin-Hub
Tests all 6 API integrations and reports their status
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
import requests
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    """Print formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")

def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}[OK] {text}{Colors.RESET}")

def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}[ERROR] {text}{Colors.RESET}")

def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}[WARN] {text}{Colors.RESET}")

def print_info(text: str):
    """Print info message"""
    print(f"{Colors.BLUE}[INFO] {text}{Colors.RESET}")


class APITester:
    """Base class for API testing"""

    def __init__(self, name: str, api_key_env: str):
        self.name = name
        self.api_key = os.getenv(api_key_env)
        self.results = {
            "name": name,
            "status": "unknown",
            "response_time": 0,
            "error": None,
            "data_sample": None
        }

    def test(self) -> Dict:
        """Run the API test - to be implemented by subclasses"""
        raise NotImplementedError


class AlphaVantageTest(APITester):
    """Test Alpha Vantage API"""

    def __init__(self):
        super().__init__("Alpha Vantage", "ALPHA_VANTAGE_API_KEY")

    def test(self) -> Dict:
        try:
            start_time = time.time()

            # Test with a simple quote request
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": "AAPL",
                "apikey": self.api_key
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            self.results["response_time"] = time.time() - start_time
            data = response.json()

            if "Global Quote" in data and data["Global Quote"]:
                quote = data["Global Quote"]
                self.results["status"] = "success"
                self.results["data_sample"] = {
                    "symbol": quote.get("01. symbol"),
                    "price": quote.get("05. price"),
                    "change": quote.get("09. change"),
                    "change_percent": quote.get("10. change percent")
                }
                print_success(f"Alpha Vantage: AAPL @ ${quote.get('05. price')} ({quote.get('10. change percent')})")
            elif "Note" in data:
                self.results["status"] = "rate_limited"
                self.results["error"] = "API rate limit reached"
                print_warning("Alpha Vantage: Rate limit reached (5 calls/min on free tier)")
            else:
                self.results["status"] = "error"
                self.results["error"] = str(data)
                print_error(f"Alpha Vantage: Unexpected response format")

        except Exception as e:
            self.results["status"] = "error"
            self.results["error"] = str(e)
            print_error(f"Alpha Vantage: {str(e)}")

        return self.results


class NewsAPITest(APITester):
    """Test News API"""

    def __init__(self):
        super().__init__("News API", "NEWS_API_KEY")

    def test(self) -> Dict:
        try:
            start_time = time.time()

            url = "https://newsapi.org/v2/everything"
            params = {
                "q": "stock market",
                "sortBy": "publishedAt",
                "pageSize": 5,
                "apiKey": self.api_key
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            self.results["response_time"] = time.time() - start_time
            data = response.json()

            if data.get("status") == "ok" and data.get("articles"):
                self.results["status"] = "success"
                self.results["data_sample"] = {
                    "total_results": data.get("totalResults"),
                    "articles_count": len(data.get("articles", [])),
                    "latest_headline": data["articles"][0].get("title") if data["articles"] else None
                }
                print_success(f"News API: Found {data.get('totalResults')} articles")
                print_info(f"  Latest: {data['articles'][0].get('title')[:60]}...")
            else:
                self.results["status"] = "error"
                self.results["error"] = data.get("message", "Unknown error")
                print_error(f"News API: {data.get('message', 'Unknown error')}")

        except Exception as e:
            self.results["status"] = "error"
            self.results["error"] = str(e)
            print_error(f"News API: {str(e)}")

        return self.results


class CoinGeckoTest(APITester):
    """Test CoinGecko API"""

    def __init__(self):
        super().__init__("CoinGecko", "COINGECKO_API_KEY")

    def test(self) -> Dict:
        try:
            start_time = time.time()

            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {
                "ids": "bitcoin,ethereum",
                "vs_currencies": "usd",
                "include_24hr_change": "true"
            }
            headers = {
                "x-cg-pro-api-key": self.api_key
            }

            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()

            self.results["response_time"] = time.time() - start_time
            data = response.json()

            if "bitcoin" in data and "ethereum" in data:
                self.results["status"] = "success"
                self.results["data_sample"] = {
                    "bitcoin": data["bitcoin"],
                    "ethereum": data["ethereum"]
                }
                print_success(f"CoinGecko: BTC ${data['bitcoin']['usd']:,.2f} ({data['bitcoin']['usd_24h_change']:.2f}%)")
                print_success(f"           ETH ${data['ethereum']['usd']:,.2f} ({data['ethereum']['usd_24h_change']:.2f}%)")
            else:
                self.results["status"] = "error"
                self.results["error"] = "Unexpected response format"
                print_error("CoinGecko: Unexpected response format")

        except Exception as e:
            self.results["status"] = "error"
            self.results["error"] = str(e)
            print_error(f"CoinGecko: {str(e)}")

        return self.results


class FREDTest(APITester):
    """Test FRED API"""

    def __init__(self):
        super().__init__("FRED", "FRED_API_KEY")

    def test(self) -> Dict:
        try:
            start_time = time.time()

            # Test with GDP data
            url = "https://api.stlouisfed.org/fred/series/observations"
            params = {
                "series_id": "GDP",
                "api_key": self.api_key,
                "file_type": "json",
                "sort_order": "desc",
                "limit": 1
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            self.results["response_time"] = time.time() - start_time
            data = response.json()

            if "observations" in data and data["observations"]:
                obs = data["observations"][0]
                self.results["status"] = "success"
                self.results["data_sample"] = {
                    "series": "GDP",
                    "date": obs.get("date"),
                    "value": obs.get("value")
                }
                print_success(f"FRED: Latest GDP (Q{obs.get('date')}): ${obs.get('value')} billion")
            else:
                self.results["status"] = "error"
                self.results["error"] = "No observations found"
                print_error("FRED: No observations found")

        except Exception as e:
            self.results["status"] = "error"
            self.results["error"] = str(e)
            print_error(f"FRED: {str(e)}")

        return self.results


class OpenSanctionsTest(APITester):
    """Test OpenSanctions API"""

    def __init__(self):
        super().__init__("OpenSanctions", "OPENSANCTIONS_API_KEY")

    def test(self) -> Dict:
        try:
            start_time = time.time()

            # Test with a search query
            url = "https://api.opensanctions.org/search/default"
            params = {
                "q": "Putin"
            }
            headers = {
                "Authorization": f"ApiKey {self.api_key}"
            }

            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()

            self.results["response_time"] = time.time() - start_time
            data = response.json()

            if "results" in data:
                self.results["status"] = "success"
                self.results["data_sample"] = {
                    "total": data.get("total"),
                    "results_count": len(data.get("results", []))
                }
                print_success(f"OpenSanctions: Found {data.get('total')} entities")
            else:
                self.results["status"] = "error"
                self.results["error"] = "Unexpected response format"
                print_error("OpenSanctions: Unexpected response format")

        except Exception as e:
            self.results["status"] = "error"
            self.results["error"] = str(e)
            print_error(f"OpenSanctions: {str(e)}")

        return self.results


class MarketStackTest(APITester):
    """Test MarketStack API"""

    def __init__(self):
        super().__init__("MarketStack", "MARKETSTACK_API_KEY")

    def test(self) -> Dict:
        try:
            start_time = time.time()

            url = "http://api.marketstack.com/v1/eod/latest"
            params = {
                "access_key": self.api_key,
                "symbols": "AAPL",
                "limit": 1
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            self.results["response_time"] = time.time() - start_time
            data = response.json()

            if "data" in data and data["data"]:
                stock = data["data"][0]
                self.results["status"] = "success"
                self.results["data_sample"] = {
                    "symbol": stock.get("symbol"),
                    "close": stock.get("close"),
                    "date": stock.get("date")
                }
                print_success(f"MarketStack: AAPL closed at ${stock.get('close')} on {stock.get('date')}")
            else:
                self.results["status"] = "error"
                self.results["error"] = data.get("error", {}).get("message", "Unknown error")
                print_error(f"MarketStack: {data.get('error', {}).get('message', 'Unknown error')}")

        except Exception as e:
            self.results["status"] = "error"
            self.results["error"] = str(e)
            print_error(f"MarketStack: {str(e)}")

        return self.results


def main():
    """Run all API tests"""
    print_header("Fin-Hub API Integration Test Suite")
    print_info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Initialize all testers
    testers = [
        AlphaVantageTest(),
        NewsAPITest(),
        CoinGeckoTest(),
        FREDTest(),
        OpenSanctionsTest(),
        MarketStackTest()
    ]

    # Run tests
    results = []
    for tester in testers:
        print(f"\n{Colors.BOLD}Testing {tester.name}...{Colors.RESET}")
        result = tester.test()
        results.append(result)
        time.sleep(1)  # Rate limiting between tests

    # Print summary
    print_header("Test Summary")

    success_count = sum(1 for r in results if r["status"] == "success")
    rate_limited_count = sum(1 for r in results if r["status"] == "rate_limited")
    error_count = sum(1 for r in results if r["status"] == "error")

    print(f"\n{Colors.BOLD}Results:{Colors.RESET}")
    print(f"  {Colors.GREEN}[OK] Successful: {success_count}/6{Colors.RESET}")
    if rate_limited_count > 0:
        print(f"  {Colors.YELLOW}[WARN] Rate Limited: {rate_limited_count}/6{Colors.RESET}")
    if error_count > 0:
        print(f"  {Colors.RED}[ERROR] Failed: {error_count}/6{Colors.RESET}")

    print(f"\n{Colors.BOLD}Response Times:{Colors.RESET}")
    for result in results:
        if result["response_time"] > 0:
            color = Colors.GREEN if result["response_time"] < 1 else Colors.YELLOW
            print(f"  {result['name']}: {color}{result['response_time']:.3f}s{Colors.RESET}")

    # Save results to file
    output_dir = Path(__file__).parent.parent / "data"
    output_file = output_dir / "api_test_results.json"

    test_report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total": len(results),
            "successful": success_count,
            "rate_limited": rate_limited_count,
            "failed": error_count
        },
        "results": results
    }

    with open(output_file, 'w') as f:
        json.dump(test_report, f, indent=2)

    print(f"\n{Colors.BLUE}Full results saved to: {output_file}{Colors.RESET}")

    # Exit code
    if error_count > 0:
        print(f"\n{Colors.RED}Some tests failed. Please check the errors above.{Colors.RESET}")
        sys.exit(1)
    else:
        print(f"\n{Colors.GREEN}All tests passed successfully!{Colors.RESET}")
        sys.exit(0)


if __name__ == "__main__":
    main()
