"""
Twelve Data API 클라이언트
멀티애셋 통합 데이터 제공 (주식, 외환, 암호화폐, 상품, ETF, 지수)
"""

import asyncio
import aiohttp
import websockets
import json
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class TwelveDataAssetClass(Enum):
    """Twelve Data 자산 클래스"""
    STOCKS = "stocks"
    FOREX = "forex"
    CRYPTOCURRENCIES = "cryptocurrencies"
    ETF = "etf"
    INDICES = "indices"
    COMMODITIES = "commodities"
    BONDS = "bonds"
    FUNDS = "funds"


class TwelveDataInterval(Enum):
    """시간 간격"""
    MIN_1 = "1min"
    MIN_5 = "5min"
    MIN_15 = "15min"
    MIN_30 = "30min"
    MIN_45 = "45min"
    HOUR_1 = "1h"
    HOUR_2 = "2h"
    HOUR_4 = "4h"
    DAY_1 = "1day"
    WEEK_1 = "1week"
    MONTH_1 = "1month"


@dataclass
class TwelveDataQuote:
    """Twelve Data 시세 데이터"""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: Optional[int] = None


@dataclass
class TwelveDataRealTime:
    """실시간 데이터"""
    symbol: str
    price: float
    change: float
    percent_change: float
    high: float
    low: float
    volume: Optional[int] = None
    previous_close: Optional[float] = None
    timestamp: Optional[datetime] = None


@dataclass
class TwelveDataTechnicals:
    """기술적 지표 데이터"""
    symbol: str
    indicator: str
    values: List[Dict[str, Any]]
    meta: Dict[str, Any]


class TwelveDataClient:
    """Twelve Data API 클라이언트"""

    BASE_URL = "https://api.twelvedata.com"
    WS_URL = "wss://ws.twelvedata.com/v1/quotes/price"

    def __init__(self, api_key: str, plan_type: str = "basic"):
        self.api_key = api_key
        self.plan_type = plan_type
        self.session: Optional[aiohttp.ClientSession] = None
        self.ws_connection: Optional[websockets.WebSocketServerProtocol] = None

        # Rate limits by plan
        self.rate_limits = {
            "basic": {"requests_per_minute": 8, "delay": 7.5},
            "grow": {"requests_per_minute": 300, "delay": 0.2},
            "pro": {"requests_per_minute": 800, "delay": 0.075},
            "enterprise": {"requests_per_minute": 8000, "delay": 0.0075}
        }
        self.request_delay = self.rate_limits.get(plan_type,
                                                self.rate_limits["basic"])["delay"]

    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        if self.session:
            await self.session.close()
        if self.ws_connection:
            await self.ws_connection.close()

    async def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict:
        """HTTP API 요청"""
        if not self.session:
            self.session = aiohttp.ClientSession()

        url = f"{self.BASE_URL}{endpoint}"
        params = params or {}
        params["apikey"] = self.api_key

        try:
            await asyncio.sleep(self.request_delay)  # Rate limiting

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"Twelve Data API error {response.status}: {error_text}")

        except Exception as e:
            logger.error(f"Twelve Data API request failed: {e}")
            raise

    async def get_time_series(self, symbol: str, interval: str = "1day",
                            outputsize: int = 5000, start_date: str = None,
                            end_date: str = None) -> List[TwelveDataQuote]:
        """시계열 데이터 조회"""
        endpoint = "/time_series"
        params = {
            "symbol": symbol,
            "interval": interval,
            "outputsize": outputsize
        }

        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        try:
            response = await self._make_request(endpoint, params)

            if "values" not in response:
                logger.warning(f"No values in response for {symbol}")
                return []

            quotes = []
            for item in response["values"]:
                quote = TwelveDataQuote(
                    symbol=symbol,
                    timestamp=datetime.fromisoformat(item["datetime"]),
                    open=float(item["open"]),
                    high=float(item["high"]),
                    low=float(item["low"]),
                    close=float(item["close"]),
                    volume=int(item["volume"]) if item.get("volume") else None
                )
                quotes.append(quote)

            return quotes[::-1]  # 시간순 정렬

        except Exception as e:
            logger.error(f"Error fetching time series for {symbol}: {e}")
            return []

    async def get_real_time_price(self, symbol: str) -> Optional[TwelveDataRealTime]:
        """실시간 가격 조회"""
        endpoint = "/price"
        params = {"symbol": symbol}

        try:
            response = await self._make_request(endpoint, params)

            return TwelveDataRealTime(
                symbol=symbol,
                price=float(response["price"]),
                change=0.0,  # Basic plan doesn't include change
                percent_change=0.0,
                high=0.0,
                low=0.0,
                timestamp=datetime.now()
            )

        except Exception as e:
            logger.error(f"Error fetching real-time price for {symbol}: {e}")
            return None

    async def get_quote(self, symbol: str) -> Optional[TwelveDataRealTime]:
        """상세 시세 조회"""
        endpoint = "/quote"
        params = {"symbol": symbol}

        try:
            response = await self._make_request(endpoint, params)

            return TwelveDataRealTime(
                symbol=response["symbol"],
                price=float(response["close"]),
                change=float(response.get("change", 0)),
                percent_change=float(response.get("percent_change", 0)),
                high=float(response["high"]),
                low=float(response["low"]),
                volume=int(response.get("volume", 0)) if response.get("volume") else None,
                previous_close=float(response.get("previous_close", 0)),
                timestamp=datetime.fromisoformat(response["datetime"])
            )

        except Exception as e:
            logger.error(f"Error fetching quote for {symbol}: {e}")
            return None

    async def get_forex_pairs(self, base_currency: str = "USD") -> List[str]:
        """외환 쌍 목록 조회"""
        endpoint = "/forex_pairs"
        params = {"base": base_currency}

        try:
            response = await self._make_request(endpoint, params)
            return [pair["symbol"] for pair in response.get("data", [])]

        except Exception as e:
            logger.error(f"Error fetching forex pairs: {e}")
            return []

    async def get_crypto_list(self) -> List[Dict[str, str]]:
        """암호화폐 목록 조회"""
        endpoint = "/cryptocurrencies"

        try:
            response = await self._make_request(endpoint)
            return response.get("data", [])

        except Exception as e:
            logger.error(f"Error fetching crypto list: {e}")
            return []

    async def get_stocks_list(self, country: str = "United States",
                            exchange: str = None) -> List[Dict[str, str]]:
        """주식 목록 조회"""
        endpoint = "/stocks"
        params = {"country": country}

        if exchange:
            params["exchange"] = exchange

        try:
            response = await self._make_request(endpoint, params)
            return response.get("data", [])

        except Exception as e:
            logger.error(f"Error fetching stocks list: {e}")
            return []

    async def get_etf_list(self, country: str = "United States") -> List[Dict[str, str]]:
        """ETF 목록 조회"""
        endpoint = "/etf"
        params = {"country": country}

        try:
            response = await self._make_request(endpoint, params)
            return response.get("data", [])

        except Exception as e:
            logger.error(f"Error fetching ETF list: {e}")
            return []

    async def get_technical_indicator(self, symbol: str, indicator: str,
                                    interval: str = "1day", time_period: int = 14,
                                    outputsize: int = 5000) -> Optional[TwelveDataTechnicals]:
        """기술적 지표 계산"""
        endpoint = f"/{indicator.lower()}"
        params = {
            "symbol": symbol,
            "interval": interval,
            "time_period": time_period,
            "outputsize": outputsize
        }

        try:
            response = await self._make_request(endpoint, params)

            if "values" not in response:
                return None

            return TwelveDataTechnicals(
                symbol=symbol,
                indicator=indicator,
                values=response["values"],
                meta=response.get("meta", {})
            )

        except Exception as e:
            logger.error(f"Error fetching {indicator} for {symbol}: {e}")
            return None

    async def get_market_movers(self, direction: str = "gainers",
                              change_type: str = "percent") -> List[Dict[str, Any]]:
        """시장 상승/하락주 조회"""
        endpoint = "/market_movers"
        params = {
            "direction": direction,  # gainers, losers
            "change_type": change_type  # percent, value
        }

        try:
            response = await self._make_request(endpoint, params)
            return response.get("values", [])

        except Exception as e:
            logger.error(f"Error fetching market movers: {e}")
            return []

    async def get_economic_calendar(self, start_date: str = None,
                                  end_date: str = None,
                                  country: str = None) -> List[Dict[str, Any]]:
        """경제 캘린더 조회"""
        endpoint = "/economic_calendar"
        params = {}

        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if country:
            params["country"] = country

        try:
            response = await self._make_request(endpoint, params)
            return response.get("data", [])

        except Exception as e:
            logger.error(f"Error fetching economic calendar: {e}")
            return []

    async def start_websocket_stream(self, symbols: List[str], callback):
        """WebSocket 실시간 스트림"""
        try:
            self.ws_connection = await websockets.connect(self.WS_URL)

            # 구독 메시지
            subscribe_msg = {
                "action": "subscribe",
                "params": {
                    "symbols": ",".join(symbols)
                }
            }
            await self.ws_connection.send(json.dumps(subscribe_msg))

            # 메시지 수신 루프
            async for message in self.ws_connection:
                try:
                    data = json.loads(message)
                    await callback(data)
                except Exception as e:
                    logger.error(f"WebSocket message handling error: {e}")

        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")

    async def get_multiple_quotes(self, symbols: List[str]) -> Dict[str, TwelveDataRealTime]:
        """다중 시세 조회"""
        endpoint = "/quote"
        symbols_str = ",".join(symbols)
        params = {"symbol": symbols_str}

        try:
            response = await self._make_request(endpoint, params)

            result = {}
            # 단일 심볼인 경우
            if isinstance(response, dict) and "symbol" in response:
                symbol = response["symbol"]
                result[symbol] = TwelveDataRealTime(
                    symbol=symbol,
                    price=float(response["close"]),
                    change=float(response.get("change", 0)),
                    percent_change=float(response.get("percent_change", 0)),
                    high=float(response["high"]),
                    low=float(response["low"]),
                    volume=int(response.get("volume", 0)) if response.get("volume") else None,
                    previous_close=float(response.get("previous_close", 0)),
                    timestamp=datetime.fromisoformat(response["datetime"])
                )
            # 다중 심볼인 경우
            elif isinstance(response, dict):
                for symbol, data in response.items():
                    if isinstance(data, dict) and "close" in data:
                        result[symbol] = TwelveDataRealTime(
                            symbol=symbol,
                            price=float(data["close"]),
                            change=float(data.get("change", 0)),
                            percent_change=float(data.get("percent_change", 0)),
                            high=float(data["high"]),
                            low=float(data["low"]),
                            volume=int(data.get("volume", 0)) if data.get("volume") else None,
                            previous_close=float(data.get("previous_close", 0)),
                            timestamp=datetime.fromisoformat(data["datetime"])
                        )

            return result

        except Exception as e:
            logger.error(f"Error fetching multiple quotes: {e}")
            return {}


class TwelveDataConverter:
    """Twelve Data를 표준 포맷으로 변환"""

    @staticmethod
    def to_dataframe(quotes: List[TwelveDataQuote]) -> pd.DataFrame:
        """TwelveDataQuote 리스트를 DataFrame으로 변환"""
        if not quotes:
            return pd.DataFrame()

        data = []
        for quote in quotes:
            data.append({
                'timestamp': quote.timestamp,
                'open': quote.open,
                'high': quote.high,
                'low': quote.low,
                'close': quote.close,
                'volume': quote.volume
            })

        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        return df

    @staticmethod
    def calculate_multi_asset_metrics(data: Dict[str, List[TwelveDataQuote]]) -> Dict[str, Dict[str, float]]:
        """다중 자산 성능 지표 계산"""
        results = {}

        for symbol, quotes in data.items():
            if not quotes:
                continue

            df = TwelveDataConverter.to_dataframe(quotes)
            if df.empty:
                continue

            returns = df['close'].pct_change().dropna()

            results[symbol] = {
                'current_price': df['close'].iloc[-1],
                'total_return': (df['close'].iloc[-1] / df['close'].iloc[0] - 1) * 100,
                'volatility': returns.std() * np.sqrt(252) * 100,
                'sharpe_ratio': returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0,
                'max_drawdown': ((df['close'] / df['close'].cummax()) - 1).min() * 100,
                'correlation_spy': 0.0  # SPY와의 상관관계 (별도 계산 필요)
            }

        return results


async def demo_twelve_data_client():
    """Twelve Data 클라이언트 데모"""
    # 실제 API 키 필요
    API_KEY = "YOUR_TWELVE_DATA_API_KEY"

    async with TwelveDataClient(API_KEY, "basic") as client:
        # 1. 주식 데이터
        print("📈 Fetching AAPL stock data...")
        aapl_data = await client.get_time_series("AAPL", "1day", 100)
        if aapl_data:
            df = TwelveDataConverter.to_dataframe(aapl_data)
            print(f"AAPL: Latest close = ${df['close'].iloc[-1]:.2f}")

        # 2. 외환 데이터
        print("💱 Fetching EUR/USD...")
        eurusd_data = await client.get_time_series("EUR/USD", "1h", 50)
        if eurusd_data:
            eur_df = TwelveDataConverter.to_dataframe(eurusd_data)
            print(f"EUR/USD: {eur_df['close'].iloc[-1]:.5f}")

        # 3. 암호화폐 데이터
        print("🪙 Fetching Bitcoin data...")
        btc_data = await client.get_time_series("BTC/USD", "1day", 50)
        if btc_data:
            btc_df = TwelveDataConverter.to_dataframe(btc_data)
            print(f"BTC/USD: ${btc_df['close'].iloc[-1]:,.2f}")

        # 4. 다중 자산 분석
        print("📊 Multi-asset analysis...")
        symbols = ["AAPL", "GOOGL", "EUR/USD", "BTC/USD"]
        multi_data = {}

        for symbol in symbols:
            data = await client.get_time_series(symbol, "1day", 100)
            if data:
                multi_data[symbol] = data

        if multi_data:
            metrics = TwelveDataConverter.calculate_multi_asset_metrics(multi_data)
            for symbol, metric in metrics.items():
                print(f"{symbol}: Return={metric['total_return']:.2f}%, Vol={metric['volatility']:.2f}%")


if __name__ == "__main__":
    asyncio.run(demo_twelve_data_client())