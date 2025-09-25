#!/usr/bin/env python3
"""
Direct Alpha Vantage API Test
Test the Alpha Vantage API directly to verify the key works
"""
import asyncio
import aiohttp
import json
from datetime import datetime

# API Configuration
API_KEY = "26PNNX3GELI0JE1W"
BASE_URL = "https://www.alphavantage.co/query"
TEST_SYMBOL = "AAPL"

async def test_alpha_vantage_api():
    """Test Alpha Vantage API directly"""

    print("🔑 Testing Alpha Vantage API with provided key")
    print(f"API Key: {API_KEY}")
    print(f"Test Symbol: {TEST_SYMBOL}")
    print("-" * 60)

    async with aiohttp.ClientSession() as session:
        # Test 1: Real-time Quote
        print("1️⃣ Testing Real-time Quote (GLOBAL_QUOTE)...")
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': TEST_SYMBOL,
            'apikey': API_KEY
        }

        try:
            async with session.get(BASE_URL, params=params) as response:
                data = await response.json()

                if 'Global Quote' in data:
                    quote = data['Global Quote']
                    symbol = quote.get('01. symbol', 'N/A')
                    price = quote.get('05. price', 'N/A')
                    change = quote.get('09. change', 'N/A')
                    change_percent = quote.get('10. change percent', 'N/A')
                    volume = quote.get('06. volume', 'N/A')

                    print(f"   ✅ SUCCESS! Got real-time data for {symbol}")
                    print(f"   💰 Price: ${price}")
                    print(f"   📈 Change: {change} ({change_percent})")
                    print(f"   📊 Volume: {volume:,}" if volume != 'N/A' else f"   📊 Volume: {volume}")

                elif 'Note' in data:
                    print(f"   ⚠️  API Rate Limited: {data['Note']}")
                elif 'Error Message' in data:
                    print(f"   ❌ API Error: {data['Error Message']}")
                else:
                    print(f"   ❓ Unexpected response: {json.dumps(data, indent=2)}")

        except Exception as e:
            print(f"   ❌ Request failed: {e}")

        # Test 2: Daily Time Series
        print("\n2️⃣ Testing Daily Time Series (TIME_SERIES_DAILY)...")
        params = {
            'function': 'TIME_SERIES_DAILY',
            'symbol': TEST_SYMBOL,
            'outputsize': 'compact',
            'apikey': API_KEY
        }

        try:
            async with session.get(BASE_URL, params=params) as response:
                data = await response.json()

                if 'Time Series (Daily)' in data:
                    time_series = data['Time Series (Daily)']
                    latest_date = sorted(time_series.keys())[-1]
                    latest_data = time_series[latest_date]

                    print(f"   ✅ SUCCESS! Got daily data for {TEST_SYMBOL}")
                    print(f"   📅 Latest Date: {latest_date}")
                    print(f"   🔓 Open: ${latest_data.get('1. open', 'N/A')}")
                    print(f"   🔒 Close: ${latest_data.get('4. close', 'N/A')}")
                    print(f"   📊 Volume: {latest_data.get('5. volume', 'N/A')}")
                    print(f"   📈 Available days: {len(time_series)}")

                elif 'Note' in data:
                    print(f"   ⚠️  API Rate Limited: {data['Note']}")
                elif 'Error Message' in data:
                    print(f"   ❌ API Error: {data['Error Message']}")
                else:
                    print(f"   ❓ Unexpected response keys: {list(data.keys())}")

        except Exception as e:
            print(f"   ❌ Request failed: {e}")

        # Test 3: Company Overview
        print("\n3️⃣ Testing Company Overview...")
        params = {
            'function': 'OVERVIEW',
            'symbol': TEST_SYMBOL,
            'apikey': API_KEY
        }

        try:
            async with session.get(BASE_URL, params=params) as response:
                data = await response.json()

                if 'Symbol' in data and data['Symbol']:
                    print(f"   ✅ SUCCESS! Got company data for {data['Symbol']}")
                    print(f"   🏢 Company: {data.get('Name', 'N/A')}")
                    print(f"   🏭 Sector: {data.get('Sector', 'N/A')}")
                    print(f"   💼 Market Cap: {data.get('MarketCapitalization', 'N/A')}")
                    print(f"   📊 P/E Ratio: {data.get('PERatio', 'N/A')}")

                elif 'Note' in data:
                    print(f"   ⚠️  API Rate Limited: {data['Note']}")
                elif 'Error Message' in data:
                    print(f"   ❌ API Error: {data['Error Message']}")
                else:
                    print(f"   ❓ Unexpected response keys: {list(data.keys())}")

        except Exception as e:
            print(f"   ❌ Request failed: {e}")

        # Test 4: Technical Indicator (RSI)
        print("\n4️⃣ Testing Technical Indicator (RSI)...")
        params = {
            'function': 'RSI',
            'symbol': TEST_SYMBOL,
            'interval': 'daily',
            'time_period': 14,
            'series_type': 'close',
            'apikey': API_KEY
        }

        try:
            async with session.get(BASE_URL, params=params) as response:
                data = await response.json()

                if 'Technical Analysis: RSI' in data:
                    rsi_data = data['Technical Analysis: RSI']
                    latest_date = sorted(rsi_data.keys())[-1]
                    latest_rsi = rsi_data[latest_date]['RSI']

                    print(f"   ✅ SUCCESS! Got RSI data for {TEST_SYMBOL}")
                    print(f"   📅 Latest Date: {latest_date}")
                    print(f"   📊 RSI Value: {latest_rsi}")
                    print(f"   📈 Available periods: {len(rsi_data)}")

                elif 'Note' in data:
                    print(f"   ⚠️  API Rate Limited: {data['Note']}")
                elif 'Error Message' in data:
                    print(f"   ❌ API Error: {data['Error Message']}")
                else:
                    print(f"   ❓ Unexpected response keys: {list(data.keys())}")

        except Exception as e:
            print(f"   ❌ Request failed: {e}")

def print_summary():
    """Print test summary and next steps"""
    print("\n" + "="*60)
    print("📊 Alpha Vantage API Test Summary")
    print("="*60)
    print("✅ If all tests passed, your API key is working correctly!")
    print("⚠️  If you see rate limiting, that's normal for free tier")
    print("❌ If you see errors, check your API key or network connection")
    print("\n🔑 API Key Info:")
    print("   - Free tier: 25 API calls per day, 5 per minute")
    print("   - Premium: Unlimited calls, real-time data")
    print("\n🚀 Next Steps:")
    print("   1. If API works, integrate with Market Spoke")
    print("   2. Test with different stock symbols")
    print("   3. Add error handling and caching")
    print("="*60)

async def main():
    """Main test function"""
    await test_alpha_vantage_api()
    print_summary()

if __name__ == "__main__":
    asyncio.run(main())