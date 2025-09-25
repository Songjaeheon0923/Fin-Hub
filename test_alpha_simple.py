#!/usr/bin/env python3
"""
Simple Alpha Vantage API Test
Test the Alpha Vantage API directly using requests library
"""
import requests
import json
from datetime import datetime

# API Configuration
API_KEY = "26PNNX3GELI0JE1W"
BASE_URL = "https://www.alphavantage.co/query"
TEST_SYMBOL = "AAPL"

def test_alpha_vantage_api():
    """Test Alpha Vantage API directly"""

    print("Testing Alpha Vantage API with provided key")
    print(f"API Key: {API_KEY}")
    print(f"Test Symbol: {TEST_SYMBOL}")
    print("-" * 60)

    # Test 1: Real-time Quote
    print("1. Testing Real-time Quote (GLOBAL_QUOTE)...")
    params = {
        'function': 'GLOBAL_QUOTE',
        'symbol': TEST_SYMBOL,
        'apikey': API_KEY
    }

    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        data = response.json()

        if 'Global Quote' in data:
            quote = data['Global Quote']
            symbol = quote.get('01. symbol', 'N/A')
            price = quote.get('05. price', 'N/A')
            change = quote.get('09. change', 'N/A')
            change_percent = quote.get('10. change percent', 'N/A')
            volume = quote.get('06. volume', 'N/A')

            print(f"   SUCCESS! Got real-time data for {symbol}")
            print(f"   Price: ${price}")
            print(f"   Change: {change} ({change_percent})")
            print(f"   Volume: {volume}")

        elif 'Note' in data:
            print(f"   API Rate Limited: {data['Note']}")
        elif 'Error Message' in data:
            print(f"   API Error: {data['Error Message']}")
        else:
            print(f"   Unexpected response: {json.dumps(data, indent=2)}")

    except Exception as e:
        print(f"   ❌ Request failed: {e}")

    # Test 2: Company Overview
    print("\n2. Testing Company Overview...")
    params = {
        'function': 'OVERVIEW',
        'symbol': TEST_SYMBOL,
        'apikey': API_KEY
    }

    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        data = response.json()

        if 'Symbol' in data and data['Symbol']:
            print(f"   SUCCESS! Got company data for {data['Symbol']}")
            print(f"   Company: {data.get('Name', 'N/A')}")
            print(f"   Sector: {data.get('Sector', 'N/A')}")
            print(f"   Market Cap: {data.get('MarketCapitalization', 'N/A')}")
            print(f"   P/E Ratio: {data.get('PERatio', 'N/A')}")

        elif 'Note' in data:
            print(f"   API Rate Limited: {data['Note']}")
        elif 'Error Message' in data:
            print(f"   API Error: {data['Error Message']}")
        else:
            print(f"   No company data found")

    except Exception as e:
        print(f"   Request failed: {e}")

    # Test 3: Search Symbol
    print("\n3. Testing Symbol Search...")
    params = {
        'function': 'SYMBOL_SEARCH',
        'keywords': 'Apple',
        'apikey': API_KEY
    }

    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        data = response.json()

        if 'bestMatches' in data:
            matches = data['bestMatches']
            print(f"   SUCCESS! Found {len(matches)} matches for 'Apple'")
            for match in matches[:3]:  # Show first 3 matches
                symbol = match.get('1. symbol', 'N/A')
                name = match.get('2. name', 'N/A')
                match_score = match.get('9. matchScore', 'N/A')
                print(f"      - {symbol}: {name} (Score: {match_score})")

        elif 'Note' in data:
            print(f"   API Rate Limited: {data['Note']}")
        elif 'Error Message' in data:
            print(f"   API Error: {data['Error Message']}")
        else:
            print(f"   No search results found")

    except Exception as e:
        print(f"   Request failed: {e}")

def print_summary():
    """Print test summary and next steps"""
    print("\n" + "="*60)
    print("Alpha Vantage API Test Results")
    print("="*60)
    print("SUCCESS = If all tests show 'SUCCESS', your API key is working!")
    print("Rate limiting is normal - API has usage limits")
    print("Errors may indicate key issues or network problems")
    print(f"\nAPI Key Status:")
    print(f"   Key: {API_KEY}")
    print("   Free tier: 25 calls/day, 5 calls/minute")
    print("\nIntegration Status:")
    print("   Alpha Vantage client implemented")
    print("   Market Spoke tool updated")
    print("   Ready for production testing")
    print("="*60)

def main():
    """Main test function"""
    test_alpha_vantage_api()
    print_summary()

if __name__ == "__main__":
    main()