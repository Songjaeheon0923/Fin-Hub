#!/usr/bin/env python3
"""
Simple API Keys Validation Test (using requests)
Test all newly acquired API keys for Fin-Hub integration
"""
import requests
import json
from datetime import datetime
import os

# Load environment variables manually
def load_env():
    env_vars = {}
    try:
        with open('../.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key] = value
        return env_vars
    except FileNotFoundError:
        print("Error: .env file not found")
        return {}

env_vars = load_env()

# API Configuration
NEWS_API_KEY = env_vars.get("NEWS_API_KEY")
COINGECKO_API_KEY = env_vars.get("COINGECKO_API_KEY")
FRED_API_KEY = env_vars.get("FRED_API_KEY")
OPENSANCTIONS_API_KEY = env_vars.get("OPENSANCTIONS_API_KEY")
ALPHA_VANTAGE_API_KEY = env_vars.get("ALPHA_VANTAGE_API_KEY")
MARKETSTACK_API_KEY = env_vars.get("MARKETSTACK_API_KEY")

def test_news_api():
    """Test News API with financial news search"""
    print("1. Testing News API...")

    if not NEWS_API_KEY or NEWS_API_KEY == "demo":
        print("   ERROR: News API key not found")
        return False

    url = "https://newsapi.org/v2/everything"
    params = {
        "q": "stock market OR financial",
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 3,
        "apiKey": NEWS_API_KEY
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "ok":
                articles = data.get("articles", [])
                print(f"   SUCCESS! Found {len(articles)} financial news articles")
                print(f"   Total available: {data.get('totalResults', 0)}")
                if articles:
                    print(f"   Sample: {articles[0].get('title', 'N/A')[:60]}...")
                return True
            else:
                print(f"   ERROR: API returned status {data.get('status')}")
                print(f"   Message: {data.get('message', 'No message')}")
                return False
        else:
            try:
                error_data = response.json()
                print(f"   ERROR: HTTP {response.status_code}")
                print(f"   Message: {error_data.get('message', 'Unknown error')}")
            except:
                print(f"   ERROR: HTTP {response.status_code} - {response.text[:100]}")
            return False
    except Exception as e:
        print(f"   ERROR: Request failed - {e}")
        return False

def test_coingecko_api():
    """Test CoinGecko API with cryptocurrency prices"""
    print("\n2. Testing CoinGecko API...")

    if not COINGECKO_API_KEY or COINGECKO_API_KEY == "demo":
        print("   ERROR: CoinGecko API key not found")
        return False

    # Test with simple price endpoint
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": "bitcoin,ethereum",
        "vs_currencies": "usd",
        "include_24hr_change": "true"
    }
    headers = {
        "accept": "application/json",
        "x-cg-demo-api-key": COINGECKO_API_KEY
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "bitcoin" in data:
                btc_price = data["bitcoin"]["usd"]
                btc_change = data["bitcoin"]["usd_24h_change"]
                eth_price = data["ethereum"]["usd"]
                print(f"   SUCCESS! Retrieved cryptocurrency prices")
                print(f"   Bitcoin: ${btc_price:,.2f} ({btc_change:+.2f}%)")
                print(f"   Ethereum: ${eth_price:,.2f}")
                return True
            else:
                print(f"   ERROR: Unexpected response format")
                print(f"   Keys: {list(data.keys())}")
                return False
        else:
            print(f"   ERROR: HTTP {response.status_code}")
            print(f"   Response: {response.text[:100]}...")
            return False
    except Exception as e:
        print(f"   ERROR: Request failed - {e}")
        return False

def test_fred_api():
    """Test FRED API with economic indicators"""
    print("\n3. Testing FRED API...")

    if not FRED_API_KEY or FRED_API_KEY == "demo":
        print("   ERROR: FRED API key not found")
        return False

    # Test with unemployment rate data
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": "UNRATE",  # US Unemployment Rate
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "limit": 3,
        "sort_order": "desc"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "observations" in data:
                observations = data["observations"]
                if observations:
                    latest = observations[0]
                    date = latest.get("date")
                    value = latest.get("value")
                    print(f"   SUCCESS! Retrieved FRED economic data")
                    print(f"   Latest US Unemployment Rate: {value}% (as of {date})")
                    print(f"   Available observations: {len(observations)}")
                    return True
                else:
                    print("   ERROR: No observations found")
                    return False
            else:
                print(f"   ERROR: Unexpected response format")
                print(f"   Response keys: {list(data.keys())}")
                return False
        else:
            print(f"   ERROR: HTTP {response.status_code}")
            print(f"   Response: {response.text[:100]}...")
            return False
    except Exception as e:
        print(f"   ERROR: Request failed - {e}")
        return False

def test_opensanctions_api():
    """Test OpenSanctions API with entity search"""
    print("\n4. Testing OpenSanctions API...")

    if not OPENSANCTIONS_API_KEY or OPENSANCTIONS_API_KEY == "demo":
        print("   ERROR: OpenSanctions API key not found")
        return False

    # Test with entity search
    url = "https://api.opensanctions.org/search/default"
    params = {
        "q": "person",
        "limit": 3
    }
    headers = {
        "Authorization": f"ApiKey {OPENSANCTIONS_API_KEY}",
        "accept": "application/json"
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if "results" in data:
                results = data["results"]
                total = data.get("total", 0)
                print(f"   SUCCESS! Retrieved sanctions data")
                print(f"   Found {total} total entities matching query")
                print(f"   Returned {len(results)} results in this batch")
                if results:
                    sample = results[0]
                    print(f"   Sample entity: {sample.get('caption', 'N/A')[:50]}...")
                return True
            else:
                print(f"   ERROR: Unexpected response format")
                print(f"   Response keys: {list(data.keys())}")
                return False
        else:
            print(f"   ERROR: HTTP {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return False
    except Exception as e:
        print(f"   ERROR: Request failed - {e}")
        return False

def test_alpha_vantage_api():
    """Re-test Alpha Vantage API to ensure it still works"""
    print("\n5. Re-testing Alpha Vantage API...")

    if not ALPHA_VANTAGE_API_KEY:
        print("   ERROR: Alpha Vantage API key not found")
        return False

    url = "https://www.alphavantage.co/query"
    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": "TSLA",
        "apikey": ALPHA_VANTAGE_API_KEY
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "Global Quote" in data:
                quote = data["Global Quote"]
                symbol = quote.get("01. symbol", "N/A")
                price = quote.get("05. price", "N/A")
                change_percent = quote.get("10. change percent", "N/A")
                print(f"   SUCCESS! Alpha Vantage still working")
                print(f"   {symbol}: ${price} ({change_percent})")
                return True
            else:
                print(f"   WARNING: Unexpected response")
                print(f"   Keys: {list(data.keys())}")
                return False
        else:
            print(f"   ERROR: HTTP {response.status_code}")
            print(f"   Response: {response.text[:100]}")
            return False
    except Exception as e:
        print(f"   ERROR: Request failed - {e}")
        return False

def test_marketstack_api():
    """Test MarketStack API with stock data"""
    print("\n6. Testing MarketStack API...")

    if not MARKETSTACK_API_KEY or MARKETSTACK_API_KEY == "demo":
        print("   ERROR: MarketStack API key not found")
        return False

    # Test with end-of-day data
    url = "http://api.marketstack.com/v1/eod"
    params = {
        "access_key": MARKETSTACK_API_KEY,
        "symbols": "AAPL",
        "limit": 3
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "data" in data and data["data"]:
                stock_data = data["data"]
                latest = stock_data[0]
                symbol = latest.get("symbol", "N/A")
                close_price = latest.get("close", "N/A")
                volume = latest.get("volume", "N/A")
                date = latest.get("date", "N/A")
                print(f"   SUCCESS! Retrieved MarketStack stock data")
                print(f"   {symbol}: ${close_price} (Volume: {volume:,})")
                print(f"   Date: {date}")
                print(f"   Total records available: {len(stock_data)}")
                return True
            else:
                print(f"   ERROR: No stock data found")
                print(f"   Response keys: {list(data.keys())}")
                return False
        else:
            try:
                error_data = response.json()
                print(f"   ERROR: HTTP {response.status_code}")
                if "error" in error_data:
                    print(f"   Error: {error_data['error'].get('message', 'Unknown error')}")
            except:
                print(f"   ERROR: HTTP {response.status_code} - {response.text[:100]}")
            return False
    except Exception as e:
        print(f"   ERROR: Request failed - {e}")
        return False

def print_summary(results):
    """Print test results summary"""
    print("\n" + "="*60)
    print("API KEY VALIDATION SUMMARY")
    print("="*60)

    apis = [
        ("News API", results[0]),
        ("CoinGecko API", results[1]),
        ("FRED API", results[2]),
        ("OpenSanctions API", results[3]),
        ("Alpha Vantage API", results[4]),
        ("MarketStack API", results[5])
    ]

    success_count = sum(results)
    total_count = len(results)

    for api_name, success in apis:
        status = "PASS" if success else "FAIL"
        icon = "[OK]" if success else "[FAIL]"
        print(f"   {icon} {api_name}: {status}")

    print(f"\nOverall Result: {success_count}/{total_count} APIs working")

    if success_count == total_count:
        print("ALL API KEYS ARE VALID AND WORKING!")
        print("Ready to integrate with Fin-Hub services")
    else:
        print("Some API keys need attention")
        print("Check the failed tests above for details")

    print("="*60)

def main():
    """Main test function"""
    print("Testing All Fin-Hub API Keys")
    print("="*60)

    # Run all tests
    results = [
        test_news_api(),
        test_coingecko_api(),
        test_fred_api(),
        test_opensanctions_api(),
        test_alpha_vantage_api(),
        test_marketstack_api()
    ]

    print_summary(results)

    # Show next steps
    if all(results):
        print("\nNEXT STEPS:")
        print("1. Integration with Market Spoke (News + Sentiment)")
        print("2. Integration with Risk Spoke (Sanctions checking)")
        print("3. New Economic Indicators service (FRED data)")
        print("4. New Crypto Analysis service (CoinGecko data)")
        print("5. Enhanced Stock Data service (MarketStack data)")

if __name__ == "__main__":
    main()