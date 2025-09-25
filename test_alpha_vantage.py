#!/usr/bin/env python3
"""
Test Alpha Vantage API Integration
Quick test to verify that Alpha Vantage integration is working
"""
import asyncio
import json
import aiohttp
import sys
import os

# Test configuration
API_BASE_URL = "http://localhost:8001"
TEST_TICKER = "AAPL"

async def test_market_spoke_price_analyzer():
    """Test the market.get_price tool with Alpha Vantage integration"""

    print("🔧 Testing Alpha Vantage API Integration with Market Spoke")
    print(f"API Base URL: {API_BASE_URL}")
    print(f"Test Ticker: {TEST_TICKER}")
    print("-" * 60)

    # Test payload for MCP call
    test_payload = {
        "jsonrpc": "2.0",
        "id": "test_1",
        "method": "tools/call",
        "params": {
            "name": "market.get_price",
            "arguments": {
                "ticker": TEST_TICKER,
                "period": "1d",
                "analysis_depth": "comprehensive",
                "include_fundamentals": True,
                "include_technical": True
            }
        }
    }

    try:
        async with aiohttp.ClientSession() as session:
            # Test 1: Health check
            print("1️⃣ Testing service health...")
            async with session.get(f"{API_BASE_URL}/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    print(f"   ✅ Service is healthy: {health_data.get('status', 'unknown')}")
                else:
                    print(f"   ❌ Service unhealthy: HTTP {response.status}")
                    return

            # Test 2: List available tools
            print("\n2️⃣ Testing tools list...")
            async with session.get(f"{API_BASE_URL}/tools") as response:
                if response.status == 200:
                    tools_data = await response.json()
                    tools = tools_data.get('tools', [])
                    print(f"   ✅ Found {len(tools)} tools:")
                    for tool in tools:
                        print(f"      - {tool.get('name', 'Unknown')}: {tool.get('description', 'No description')}")
                else:
                    print(f"   ❌ Failed to get tools: HTTP {response.status}")

            # Test 3: Call market.get_price tool via MCP endpoint
            print(f"\n3️⃣ Testing market.get_price tool for {TEST_TICKER}...")
            async with session.post(f"{API_BASE_URL}/mcp",
                                   json=test_payload,
                                   headers={"Content-Type": "application/json"}) as response:

                if response.status == 200:
                    response_data = await response.json()

                    if "result" in response_data:
                        result = response_data["result"]
                        content = result.get("content", [])

                        if content and content[0].get("type") == "text":
                            data = json.loads(content[0]["text"])

                            # Check if we got Alpha Vantage data or fallback
                            if data.get("success"):
                                tool_data = data.get("data", {})
                                data_source = tool_data.get("data_source", "unknown")

                                print(f"   ✅ Successfully got data from: {data_source}")

                                # Show current price info
                                if "current" in tool_data:
                                    current = tool_data["current"]
                                    price = current.get("price", "N/A")
                                    change = current.get("change", "N/A")
                                    print(f"   💰 Current Price: ${price}")
                                    print(f"   📈 Change: {change}")

                                # Check if we got real API data or fallback
                                if "Alpha Vantage" in data_source:
                                    print(f"   🎉 Using REAL Alpha Vantage API data!")
                                else:
                                    print(f"   ⚠️  Using fallback/mock data (API may be rate limited)")

                                # Show fundamentals if available
                                if "fundamentals" in tool_data and tool_data["fundamentals"]:
                                    fund = tool_data["fundamentals"]
                                    print(f"   🏢 Company: {fund.get('company_name', 'N/A')}")
                                    print(f"   🏭 Sector: {fund.get('sector', 'N/A')}")
                                    print(f"   💼 Market Cap: {fund.get('market_cap', 'N/A')}")

                                # Show technical indicators if available
                                if "technical_indicators" in tool_data and tool_data["technical_indicators"]:
                                    ti = tool_data["technical_indicators"]
                                    if "RSI" in ti and ti["RSI"]:
                                        rsi_value = ti["RSI"][0].get("value", "N/A")
                                        print(f"   📊 RSI: {rsi_value}")

                                print(f"   🔄 Last Updated: {tool_data.get('last_updated', 'N/A')}")

                            else:
                                print(f"   ❌ Tool execution failed: {data.get('error', 'Unknown error')}")
                        else:
                            print(f"   ❌ Invalid response format")
                    else:
                        print(f"   ❌ MCP error: {response_data.get('error', 'Unknown error')}")
                else:
                    error_text = await response.text()
                    print(f"   ❌ HTTP error {response.status}: {error_text}")

            # Test 4: Direct REST API test
            print(f"\n4️⃣ Testing direct REST API call...")
            rest_payload = {
                "ticker": TEST_TICKER,
                "period": "1d",
                "analysis_depth": "basic"
            }

            async with session.post(f"{API_BASE_URL}/tools/market.get_price/execute",
                                   json=rest_payload,
                                   headers={"Content-Type": "application/json"}) as response:
                if response.status == 200:
                    rest_data = await response.json()
                    result_data = rest_data.get("result", {})
                    if result_data.get("success"):
                        data_source = result_data.get("data", {}).get("data_source", "unknown")
                        print(f"   ✅ REST API working with data source: {data_source}")
                    else:
                        print(f"   ❌ REST API failed: {result_data.get('error', 'Unknown')}")
                else:
                    print(f"   ❌ REST API HTTP error: {response.status}")

    except aiohttp.ClientError as e:
        print(f"❌ Connection error: {e}")
        print("🔧 Make sure Market Spoke service is running on port 8001")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def print_setup_instructions():
    """Print setup instructions for Alpha Vantage API"""
    print("\n" + "="*60)
    print("🔑 Alpha Vantage API Setup Instructions")
    print("="*60)
    print("1. Get your free API key from: https://www.alphavantage.co/support/#api-key")
    print("2. Set environment variable: export ALPHA_VANTAGE_API_KEY=your_key_here")
    print("3. Or add to .env file: ALPHA_VANTAGE_API_KEY=your_key_here")
    print("4. Demo key is used by default for testing")
    print("\n🚀 To run Market Spoke with Alpha Vantage:")
    print("   docker-compose up -d market-spoke")
    print("\n📊 Example API key features:")
    print("   - Free tier: 25 API calls per day")
    print("   - Premium: Unlimited calls, real-time data")
    print("="*60)

async def main():
    """Main test function"""
    if len(sys.argv) > 1 and sys.argv[1] == "--setup":
        print_setup_instructions()
        return

    await test_market_spoke_price_analyzer()
    print_setup_instructions()

if __name__ == "__main__":
    asyncio.run(main())