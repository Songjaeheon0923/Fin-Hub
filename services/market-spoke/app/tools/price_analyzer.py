"""
Price Analyzer Tool - Get stock price data with Alpha Vantage API
"""
import random
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any

# Add path for shared modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'shared'))

from .base_tool import BaseTool
from ..clients.alpha_vantage_client import AlphaVantageClient


class PriceAnalyzer(BaseTool):
    """Tool for analyzing stock prices"""

    def __init__(self):
        super().__init__(
            tool_id="market.get_price",
            name="Get Stock Price",
            description="실시간 또는 과거 주가 데이터를 조회합니다 (Alpha Vantage API 연동)"
        )
        self.alpha_vantage = AlphaVantageClient()

    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute price analysis"""
        try:
            # Validate required arguments
            self.validate_arguments(arguments, ["ticker"])

            ticker = arguments["ticker"].upper()
            period = arguments.get("period", "1d")
            analysis_depth = arguments.get("analysis_depth", "detailed")
            include_fundamentals = arguments.get("include_fundamentals", True)
            include_technical = arguments.get("include_technical", True)
            start_date = arguments.get("start_date")
            end_date = arguments.get("end_date")

            print(f"Getting price data for {ticker}, period: {period}, depth: {analysis_depth}")

            # Try Alpha Vantage API first, fallback to mock data
            try:
                # Always get real-time quote
                current_quote = await self.alpha_vantage.get_real_time_quote(ticker)

                price_data = {
                    "ticker": ticker,
                    "current": current_quote,
                    "period": period,
                    "analysis_depth": analysis_depth,
                    "last_updated": datetime.now().isoformat(),
                    "data_source": "Alpha Vantage API"
                }

                # Get historical data for all analysis depths
                if analysis_depth in ["detailed", "comprehensive"]:
                    historical_data = await self.alpha_vantage.get_historical_data(ticker, period)
                    price_data["historical"] = historical_data.get("data", [])[:20]

                # Get company fundamentals for detailed and comprehensive
                if include_fundamentals and analysis_depth in ["detailed", "comprehensive"]:
                    fundamentals = await self.alpha_vantage.get_company_fundamentals(ticker)
                    price_data["fundamentals"] = fundamentals

                # Get technical indicators only for comprehensive
                if include_technical and analysis_depth == "comprehensive":
                    rsi_data = await self.alpha_vantage.get_technical_indicators(ticker, "RSI")
                    macd_data = await self.alpha_vantage.get_technical_indicators(ticker, "MACD")
                    sma_data = await self.alpha_vantage.get_technical_indicators(ticker, "SMA")

                    price_data["technical_indicators"] = {
                        "RSI": rsi_data.get("data", [])[:5],
                        "MACD": macd_data.get("data", [])[:5],
                        "SMA": sma_data.get("data", [])[:5]
                    }

                return self.create_success_response(
                    data=price_data,
                    metadata={
                        "ticker": ticker,
                        "period": period,
                        "data_source": "alpha_vantage",
                        "api_status": "success",
                        "timestamp": datetime.now().isoformat()
                    }
                )

            except Exception as api_error:
                print(f"Alpha Vantage API error: {api_error}, falling back to mock data")
                # Fallback to mock data
                price_data = await self._get_mock_price_data(ticker, period, start_date, end_date)
                return self.create_success_response(
                    data=price_data,
                    metadata={
                        "ticker": ticker,
                        "period": period,
                        "data_source": "mock_fallback",
                        "api_status": "fallback",
                        "timestamp": datetime.now().isoformat()
                    }
                )

        except Exception as e:
            return await self.handle_error(e, "price_analysis")

    async def get_tool_info(self) -> Dict[str, Any]:
        """Get tool information for MCP schema"""
        return {
            "name": self.tool_id,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Stock ticker symbol (e.g., AAPL, TSLA, MSFT, GOOGL)",
                        "pattern": "^[A-Z]{1,5}$"
                    },
                    "period": {
                        "type": "string",
                        "description": "Time period for data (1d, 5d, 1mo, 3mo, 6mo, 1y)",
                        "enum": ["1d", "5d", "1mo", "3mo", "6mo", "1y"],
                        "default": "1d"
                    },
                    "analysis_depth": {
                        "type": "string",
                        "description": "Level of analysis detail",
                        "enum": ["basic", "detailed", "comprehensive"],
                        "default": "detailed"
                    },
                    "include_fundamentals": {
                        "type": "boolean",
                        "description": "Include company fundamental data",
                        "default": true
                    },
                    "include_technical": {
                        "type": "boolean",
                        "description": "Include technical indicators (RSI, MACD)",
                        "default": true
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date (YYYY-MM-DD format, optional)",
                        "format": "date"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date (YYYY-MM-DD format, optional)",
                        "format": "date"
                    }
                },
                "required": ["ticker"]
            }
        }

    async def _get_mock_price_data(self, ticker: str, period: str, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """Generate mock price data"""
        # Base price for different stocks (mock data)
        base_prices = {
            "AAPL": 150.0,
            "TSLA": 200.0,
            "MSFT": 300.0,
            "GOOGL": 120.0,
            "AMZN": 140.0,
            "NVDA": 400.0,
            "SPY": 450.0,
            "QQQ": 350.0
        }

        base_price = base_prices.get(ticker, 100.0)

        # Generate current price with some random variation
        current_price = base_price * (1 + random.uniform(-0.05, 0.05))
        open_price = current_price * (1 + random.uniform(-0.02, 0.02))
        high_price = max(current_price, open_price) * (1 + random.uniform(0, 0.03))
        low_price = min(current_price, open_price) * (1 - random.uniform(0, 0.03))
        volume = random.randint(1000000, 50000000)

        # Calculate change
        change = current_price - open_price
        change_percent = (change / open_price) * 100

        # Generate historical data based on period
        historical_data = await self._generate_historical_data(base_price, period)

        return {
            "ticker": ticker,
            "current": {
                "price": round(current_price, 2),
                "open": round(open_price, 2),
                "high": round(high_price, 2),
                "low": round(low_price, 2),
                "volume": volume,
                "change": round(change, 2),
                "change_percent": round(change_percent, 2),
                "currency": "USD"
            },
            "historical": historical_data,
            "period": period,
            "last_updated": datetime.now().isoformat()
        }

    async def _generate_historical_data(self, base_price: float, period: str) -> list:
        """Generate mock historical data"""
        # Determine number of data points based on period
        period_days = {
            "1d": 1,
            "5d": 5,
            "1mo": 30,
            "3mo": 90,
            "6mo": 180,
            "1y": 365
        }

        days = period_days.get(period, 30)
        data_points = min(days, 100)  # Limit to 100 data points

        historical = []
        current_price = base_price

        for i in range(data_points):
            date = datetime.now() - timedelta(days=data_points - i - 1)

            # Random walk for price
            change_percent = random.uniform(-0.03, 0.03)
            current_price *= (1 + change_percent)

            open_price = current_price * (1 + random.uniform(-0.01, 0.01))
            close_price = current_price * (1 + random.uniform(-0.01, 0.01))
            high_price = max(open_price, close_price) * (1 + random.uniform(0, 0.02))
            low_price = min(open_price, close_price) * (1 - random.uniform(0, 0.02))
            volume = random.randint(500000, 10000000)

            historical.append({
                "date": date.strftime("%Y-%m-%d"),
                "open": round(open_price, 2),
                "high": round(high_price, 2),
                "low": round(low_price, 2),
                "close": round(close_price, 2),
                "volume": volume
            })

            current_price = close_price

        return historical[-20:]  # Return last 20 data points