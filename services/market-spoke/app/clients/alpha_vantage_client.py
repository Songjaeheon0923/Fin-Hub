"""
Alpha Vantage API Client for Real-time Financial Data
"""
import asyncio
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import aiohttp
import pandas as pd
from alpha_vantage.timeseries import TimeSeries
from alpha_vantage.fundamentaldata import FundamentalData
from alpha_vantage.techindicators import TechIndicators


class AlphaVantageClient:
    """Client for Alpha Vantage API"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('ALPHA_VANTAGE_API_KEY')
        self.base_url = "https://www.alphavantage.co/query"

        if not self.api_key:
            print("Warning: No Alpha Vantage API key provided. Using demo key.")
            self.api_key = "demo"  # Demo key for testing

        # Initialize Alpha Vantage clients
        self.ts = TimeSeries(key=self.api_key, output_format='pandas')
        self.fd = FundamentalData(key=self.api_key, output_format='pandas')
        self.ti = TechIndicators(key=self.api_key, output_format='pandas')

        # Rate limiting
        self.requests_per_minute = 5 if self.api_key == "demo" else 75
        self.request_count = 0
        self.last_minute = datetime.now().minute

    async def _check_rate_limit(self):
        """Check and enforce rate limiting"""
        current_minute = datetime.now().minute

        if current_minute != self.last_minute:
            self.request_count = 0
            self.last_minute = current_minute

        if self.request_count >= self.requests_per_minute:
            print(f"Rate limit reached. Waiting...")
            await asyncio.sleep(60)
            self.request_count = 0

        self.request_count += 1

    async def get_real_time_quote(self, symbol: str) -> Dict[str, Any]:
        """Get real-time quote for a symbol"""
        await self._check_rate_limit()

        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    'function': 'GLOBAL_QUOTE',
                    'symbol': symbol,
                    'apikey': self.api_key
                }

                async with session.get(self.base_url, params=params) as response:
                    data = await response.json()

                    if 'Global Quote' in data:
                        quote = data['Global Quote']
                        return {
                            'symbol': quote.get('01. symbol', symbol),
                            'price': float(quote.get('05. price', 0)),
                            'change': float(quote.get('09. change', 0)),
                            'change_percent': quote.get('10. change percent', '0%').replace('%', ''),
                            'volume': int(quote.get('06. volume', 0)),
                            'latest_trading_day': quote.get('07. latest trading day'),
                            'previous_close': float(quote.get('08. previous close', 0)),
                            'open': float(quote.get('02. open', 0)),
                            'high': float(quote.get('03. high', 0)),
                            'low': float(quote.get('04. low', 0)),
                        }
                    else:
                        return await self._get_fallback_quote(symbol)

        except Exception as e:
            print(f"Alpha Vantage API error for {symbol}: {e}")
            return await self._get_fallback_quote(symbol)

    async def get_historical_data(self, symbol: str, period: str = "1month") -> Dict[str, Any]:
        """Get historical price data"""
        await self._check_rate_limit()

        try:
            # Use pandas-based TimeSeries
            if period in ["1day", "daily"]:
                data, metadata = self.ts.get_daily(symbol=symbol, outputsize='compact')
            elif period in ["1week", "weekly"]:
                data, metadata = self.ts.get_weekly(symbol=symbol)
            elif period in ["1month", "monthly"]:
                data, metadata = self.ts.get_monthly(symbol=symbol)
            else:
                data, metadata = self.ts.get_daily(symbol=symbol, outputsize='full')

            if data.empty:
                return await self._get_fallback_historical(symbol, period)

            # Convert to our format
            historical_data = []
            for date, row in data.head(30).iterrows():
                historical_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'open': float(row['1. open']),
                    'high': float(row['2. high']),
                    'low': float(row['3. low']),
                    'close': float(row['4. close']),
                    'volume': int(row['5. volume'])
                })

            return {
                'symbol': symbol,
                'period': period,
                'data': historical_data,
                'metadata': {
                    'last_refreshed': metadata.get('3. Last Refreshed'),
                    'time_zone': metadata.get('5. Time Zone'),
                    'data_source': 'Alpha Vantage'
                }
            }

        except Exception as e:
            print(f"Historical data error for {symbol}: {e}")
            return await self._get_fallback_historical(symbol, period)

    async def get_technical_indicators(self, symbol: str, indicator: str = "RSI") -> Dict[str, Any]:
        """Get technical indicators"""
        await self._check_rate_limit()

        try:
            if indicator.upper() == "RSI":
                data, metadata = self.ti.get_rsi(symbol=symbol, interval='daily', time_period=14)
            elif indicator.upper() == "MACD":
                data, metadata = self.ti.get_macd(symbol=symbol, interval='daily')
            elif indicator.upper() == "SMA":
                data, metadata = self.ti.get_sma(symbol=symbol, interval='daily', time_period=20)
            elif indicator.upper() == "EMA":
                data, metadata = self.ti.get_ema(symbol=symbol, interval='daily', time_period=20)
            else:
                data, metadata = self.ti.get_rsi(symbol=symbol, interval='daily')

            if data.empty:
                return await self._get_fallback_indicators(symbol, indicator)

            # Convert to our format
            indicators_data = []
            for date, row in data.head(10).iterrows():
                indicators_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'value': float(list(row.values())[0])
                })

            return {
                'symbol': symbol,
                'indicator': indicator.upper(),
                'data': indicators_data,
                'metadata': metadata
            }

        except Exception as e:
            print(f"Technical indicators error for {symbol}: {e}")
            return await self._get_fallback_indicators(symbol, indicator)

    async def get_company_fundamentals(self, symbol: str) -> Dict[str, Any]:
        """Get company fundamental data"""
        await self._check_rate_limit()

        try:
            # Get company overview
            async with aiohttp.ClientSession() as session:
                params = {
                    'function': 'OVERVIEW',
                    'symbol': symbol,
                    'apikey': self.api_key
                }

                async with session.get(self.base_url, params=params) as response:
                    data = await response.json()

                    if 'Symbol' in data and data['Symbol']:
                        return {
                            'symbol': data.get('Symbol', symbol),
                            'company_name': data.get('Name', 'Unknown'),
                            'sector': data.get('Sector', 'Unknown'),
                            'industry': data.get('Industry', 'Unknown'),
                            'market_cap': data.get('MarketCapitalization', 'N/A'),
                            'pe_ratio': data.get('PERatio', 'N/A'),
                            'peg_ratio': data.get('PEGRatio', 'N/A'),
                            'dividend_yield': data.get('DividendYield', 'N/A'),
                            '52_week_high': data.get('52WeekHigh', 'N/A'),
                            '52_week_low': data.get('52WeekLow', 'N/A'),
                            'description': data.get('Description', 'No description available')[:200] + '...'
                        }
                    else:
                        return await self._get_fallback_fundamentals(symbol)

        except Exception as e:
            print(f"Fundamentals error for {symbol}: {e}")
            return await self._get_fallback_fundamentals(symbol)

    async def search_symbols(self, keywords: str) -> List[Dict[str, Any]]:
        """Search for symbols matching keywords"""
        await self._check_rate_limit()

        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    'function': 'SYMBOL_SEARCH',
                    'keywords': keywords,
                    'apikey': self.api_key
                }

                async with session.get(self.base_url, params=params) as response:
                    data = await response.json()

                    results = []
                    if 'bestMatches' in data:
                        for match in data['bestMatches'][:10]:  # Limit to 10 results
                            results.append({
                                'symbol': match.get('1. symbol', ''),
                                'name': match.get('2. name', ''),
                                'type': match.get('3. type', ''),
                                'region': match.get('4. region', ''),
                                'market_open': match.get('5. marketOpen', ''),
                                'market_close': match.get('6. marketClose', ''),
                                'timezone': match.get('7. timezone', ''),
                                'currency': match.get('8. currency', ''),
                                'match_score': float(match.get('9. matchScore', 0))
                            })

                    return results

        except Exception as e:
            print(f"Symbol search error: {e}")
            return []

    # Fallback methods using mock data
    async def _get_fallback_quote(self, symbol: str) -> Dict[str, Any]:
        """Fallback quote data when API fails"""
        import random

        base_price = random.uniform(50, 500)
        change = random.uniform(-10, 10)

        return {
            'symbol': symbol,
            'price': round(base_price, 2),
            'change': round(change, 2),
            'change_percent': f"{round((change/base_price)*100, 2)}",
            'volume': random.randint(100000, 10000000),
            'latest_trading_day': datetime.now().strftime('%Y-%m-%d'),
            'previous_close': round(base_price - change, 2),
            'open': round(base_price + random.uniform(-5, 5), 2),
            'high': round(base_price + random.uniform(0, 10), 2),
            'low': round(base_price - random.uniform(0, 10), 2),
            'data_source': 'Fallback Mock Data'
        }

    async def _get_fallback_historical(self, symbol: str, period: str) -> Dict[str, Any]:
        """Fallback historical data"""
        import random
        from datetime import datetime, timedelta

        data = []
        base_price = random.uniform(50, 500)

        for i in range(30):
            date = datetime.now() - timedelta(days=i)
            daily_change = random.uniform(-0.05, 0.05)

            open_price = base_price * (1 + daily_change)
            high_price = open_price * (1 + random.uniform(0, 0.03))
            low_price = open_price * (1 - random.uniform(0, 0.03))
            close_price = open_price + random.uniform(-2, 2)

            data.append({
                'date': date.strftime('%Y-%m-%d'),
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'close': round(close_price, 2),
                'volume': random.randint(100000, 10000000)
            })

            base_price = close_price

        return {
            'symbol': symbol,
            'period': period,
            'data': data,
            'metadata': {
                'data_source': 'Fallback Mock Data',
                'last_refreshed': datetime.now().isoformat()
            }
        }

    async def _get_fallback_indicators(self, symbol: str, indicator: str) -> Dict[str, Any]:
        """Fallback technical indicators"""
        import random
        from datetime import datetime, timedelta

        data = []
        for i in range(10):
            date = datetime.now() - timedelta(days=i)

            if indicator.upper() == "RSI":
                value = random.uniform(20, 80)
            elif indicator.upper() == "MACD":
                value = random.uniform(-2, 2)
            else:
                value = random.uniform(50, 200)

            data.append({
                'date': date.strftime('%Y-%m-%d'),
                'value': round(value, 4)
            })

        return {
            'symbol': symbol,
            'indicator': indicator.upper(),
            'data': data,
            'metadata': {'data_source': 'Fallback Mock Data'}
        }

    async def _get_fallback_fundamentals(self, symbol: str) -> Dict[str, Any]:
        """Fallback fundamental data"""
        import random

        sectors = ['Technology', 'Healthcare', 'Financial', 'Consumer', 'Industrial']

        return {
            'symbol': symbol,
            'company_name': f'{symbol} Corporation',
            'sector': random.choice(sectors),
            'industry': f'{random.choice(sectors)} Services',
            'market_cap': f'{random.randint(1, 100)}B',
            'pe_ratio': round(random.uniform(10, 30), 2),
            'peg_ratio': round(random.uniform(0.5, 2.5), 2),
            'dividend_yield': f'{round(random.uniform(0, 5), 2)}%',
            '52_week_high': round(random.uniform(100, 200), 2),
            '52_week_low': round(random.uniform(50, 99), 2),
            'description': f'Fallback company description for {symbol}...',
            'data_source': 'Fallback Mock Data'
        }