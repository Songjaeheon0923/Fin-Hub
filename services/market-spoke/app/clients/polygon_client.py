"""
Polygon.io API 클라이언트
초저지연 실시간 데이터 제공 (<20ms)
"""

import asyncio
import aiohttp
import websockets
import json
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class PolygonDataType(Enum):
    """Polygon 데이터 타입"""
    STOCKS = "stocks"
    OPTIONS = "options"
    FOREX = "forex"
    CRYPTO = "crypto"
    INDICES = "indices"


@dataclass
class PolygonTicker:
    """Polygon 티커 데이터"""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    vwap: Optional[float] = None
    transactions: Optional[int] = None


@dataclass
class PolygonTrade:
    """Polygon 실시간 거래 데이터"""
    symbol: str
    timestamp: datetime
    price: float
    size: int
    exchange: str
    conditions: List[str] = field(default_factory=list)


@dataclass
class PolygonQuote:
    """Polygon 실시간 호가 데이터"""
    symbol: str
    timestamp: datetime
    bid: float
    ask: float
    bid_size: int
    ask_size: int
    exchange: str


class PolygonClient:
    """Polygon.io 고성능 데이터 클라이언트"""

    BASE_URL = "https://api.polygon.io"
    WS_URL = "wss://socket.polygon.io"

    def __init__(self, api_key: str, plan_type: str = "professional"):
        self.api_key = api_key
        self.plan_type = plan_type
        self.session: Optional[aiohttp.ClientSession] = None
        self.ws_connection: Optional[websockets.WebSocketServerProtocol] = None
        self.subscriptions: Dict[str, List[Callable]] = {}
        self.rate_limits = {
            "basic": {"requests_per_minute": 5, "delay": 12.0},
            "starter": {"requests_per_minute": 100, "delay": 0.6},
            "developer": {"requests_per_minute": 1000, "delay": 0.06},
            "professional": {"requests_per_minute": 10000, "delay": 0.006},
            "advanced": {"requests_per_minute": 100000, "delay": 0.0006}
        }
        self.request_delay = self.rate_limits.get(plan_type,
                                                self.rate_limits["professional"])["delay"]

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
                    raise Exception(f"Polygon API error {response.status}: {error_text}")

        except Exception as e:
            logger.error(f"Polygon API request failed: {e}")
            raise

    async def get_aggregates(self, symbol: str, multiplier: int = 1,
                           timespan: str = "day", from_date: str = None,
                           to_date: str = None, limit: int = 5000) -> List[PolygonTicker]:
        """집계 데이터 조회 (OHLCV)"""
        if not from_date:
            from_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        if not to_date:
            to_date = datetime.now().strftime("%Y-%m-%d")

        endpoint = f"/v2/aggs/ticker/{symbol}/range/{multiplier}/{timespan}/{from_date}/{to_date}"
        params = {"adjusted": "true", "sort": "asc", "limit": limit}

        try:
            response = await self._make_request(endpoint, params)
            results = response.get("results", [])

            tickers = []
            for result in results:
                ticker = PolygonTicker(
                    symbol=symbol,
                    timestamp=datetime.fromtimestamp(result["t"] / 1000),
                    open=result["o"],
                    high=result["h"],
                    low=result["l"],
                    close=result["c"],
                    volume=result["v"],
                    vwap=result.get("vw"),
                    transactions=result.get("n")
                )
                tickers.append(ticker)

            return tickers

        except Exception as e:
            logger.error(f"Error fetching aggregates for {symbol}: {e}")
            return []

    async def get_real_time_quote(self, symbol: str) -> Optional[PolygonQuote]:
        """실시간 호가 조회"""
        endpoint = f"/v1/last_quote/stocks/{symbol}"

        try:
            response = await self._make_request(endpoint)
            result = response.get("last", {})

            if result:
                return PolygonQuote(
                    symbol=symbol,
                    timestamp=datetime.fromtimestamp(result["timestamp"] / 1000000000),
                    bid=result["bid"],
                    ask=result["ask"],
                    bid_size=result["bid_size"],
                    ask_size=result["ask_size"],
                    exchange=result.get("exchange", "")
                )

        except Exception as e:
            logger.error(f"Error fetching quote for {symbol}: {e}")

        return None

    async def get_real_time_trade(self, symbol: str) -> Optional[PolygonTrade]:
        """실시간 거래 조회"""
        endpoint = f"/v1/last/stocks/{symbol}"

        try:
            response = await self._make_request(endpoint)
            result = response.get("last", {})

            if result:
                return PolygonTrade(
                    symbol=symbol,
                    timestamp=datetime.fromtimestamp(result["timestamp"] / 1000000000),
                    price=result["price"],
                    size=result["size"],
                    exchange=result.get("exchange", ""),
                    conditions=result.get("conditions", [])
                )

        except Exception as e:
            logger.error(f"Error fetching trade for {symbol}: {e}")

        return None

    async def get_forex_rates(self, from_currency: str = "USD",
                            to_currency: str = "EUR") -> Dict[str, float]:
        """외환 실시간 환율"""
        endpoint = f"/v1/last_quote/currencies/{from_currency}/{to_currency}"

        try:
            response = await self._make_request(endpoint)
            result = response.get("last", {})

            if result:
                return {
                    "bid": result["bid"],
                    "ask": result["ask"],
                    "mid": (result["bid"] + result["ask"]) / 2,
                    "timestamp": result["timestamp"]
                }

        except Exception as e:
            logger.error(f"Error fetching forex {from_currency}/{to_currency}: {e}")

        return {}

    async def get_crypto_aggregates(self, symbol: str, multiplier: int = 1,
                                  timespan: str = "day", limit: int = 5000) -> List[PolygonTicker]:
        """암호화폐 집계 데이터"""
        from_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        to_date = datetime.now().strftime("%Y-%m-%d")

        endpoint = f"/v2/aggs/ticker/X:{symbol}/range/{multiplier}/{timespan}/{from_date}/{to_date}"
        params = {"sort": "asc", "limit": limit}

        try:
            response = await self._make_request(endpoint, params)
            results = response.get("results", [])

            tickers = []
            for result in results:
                ticker = PolygonTicker(
                    symbol=f"X:{symbol}",
                    timestamp=datetime.fromtimestamp(result["t"] / 1000),
                    open=result["o"],
                    high=result["h"],
                    low=result["l"],
                    close=result["c"],
                    volume=result["v"],
                    vwap=result.get("vw")
                )
                tickers.append(ticker)

            return tickers

        except Exception as e:
            logger.error(f"Error fetching crypto aggregates for {symbol}: {e}")
            return []

    async def start_websocket_stream(self, symbols: List[str],
                                   data_types: List[str] = None):
        """WebSocket 실시간 스트림 시작"""
        if data_types is None:
            data_types = ["T", "Q"]  # Trades and Quotes

        try:
            self.ws_connection = await websockets.connect(
                f"{self.WS_URL}/stocks",
                extra_headers={"Authorization": f"Bearer {self.api_key}"}
            )

            # 인증
            auth_msg = {"action": "auth", "params": self.api_key}
            await self.ws_connection.send(json.dumps(auth_msg))

            # 구독
            for data_type in data_types:
                for symbol in symbols:
                    subscribe_msg = {
                        "action": "subscribe",
                        "params": f"{data_type}.{symbol}"
                    }
                    await self.ws_connection.send(json.dumps(subscribe_msg))

            # 메시지 수신 루프
            async for message in self.ws_connection:
                try:
                    data = json.loads(message)
                    await self._handle_websocket_message(data)
                except Exception as e:
                    logger.error(f"WebSocket message handling error: {e}")

        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")

    async def _handle_websocket_message(self, data: List[Dict]):
        """WebSocket 메시지 처리"""
        for item in data:
            event_type = item.get("ev")

            if event_type == "T":  # Trade
                trade = PolygonTrade(
                    symbol=item["sym"],
                    timestamp=datetime.fromtimestamp(item["t"] / 1000),
                    price=item["p"],
                    size=item["s"],
                    exchange=str(item.get("x", "")),
                    conditions=item.get("c", [])
                )
                await self._notify_subscribers("trade", trade)

            elif event_type == "Q":  # Quote
                quote = PolygonQuote(
                    symbol=item["sym"],
                    timestamp=datetime.fromtimestamp(item["t"] / 1000),
                    bid=item["bp"],
                    ask=item["ap"],
                    bid_size=item["bs"],
                    ask_size=item["as"],
                    exchange=str(item.get("x", ""))
                )
                await self._notify_subscribers("quote", quote)

    def subscribe_to_updates(self, event_type: str, callback: Callable):
        """실시간 업데이트 구독"""
        if event_type not in self.subscriptions:
            self.subscriptions[event_type] = []
        self.subscriptions[event_type].append(callback)

    async def _notify_subscribers(self, event_type: str, data: Any):
        """구독자들에게 알림"""
        if event_type in self.subscriptions:
            for callback in self.subscriptions[event_type]:
                try:
                    await callback(data)
                except Exception as e:
                    logger.error(f"Subscriber callback error: {e}")

    async def get_market_status(self) -> Dict[str, Any]:
        """시장 상태 조회"""
        endpoint = "/v1/marketstatus/now"

        try:
            response = await self._make_request(endpoint)
            return response
        except Exception as e:
            logger.error(f"Error fetching market status: {e}")
            return {}

    async def get_company_financials(self, symbol: str,
                                   period_type: str = "annual",
                                   limit: int = 10) -> Dict[str, Any]:
        """회사 재무제표 데이터"""
        endpoint = f"/vX/reference/financials"
        params = {
            "ticker": symbol,
            "period_type": period_type,
            "limit": limit
        }

        try:
            response = await self._make_request(endpoint, params)
            return response.get("results", [])
        except Exception as e:
            logger.error(f"Error fetching financials for {symbol}: {e}")
            return {}


class PolygonDataConverter:
    """Polygon 데이터를 표준 포맷으로 변환"""

    @staticmethod
    def to_dataframe(tickers: List[PolygonTicker]) -> pd.DataFrame:
        """PolygonTicker 리스트를 DataFrame으로 변환"""
        if not tickers:
            return pd.DataFrame()

        data = []
        for ticker in tickers:
            data.append({
                'timestamp': ticker.timestamp,
                'open': ticker.open,
                'high': ticker.high,
                'low': ticker.low,
                'close': ticker.close,
                'volume': ticker.volume,
                'vwap': ticker.vwap,
                'transactions': ticker.transactions
            })

        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        return df

    @staticmethod
    def calculate_performance_metrics(df: pd.DataFrame) -> Dict[str, float]:
        """성능 지표 계산"""
        if df.empty:
            return {}

        returns = df['close'].pct_change().dropna()

        metrics = {
            'total_return': (df['close'].iloc[-1] / df['close'].iloc[0] - 1) * 100,
            'volatility': returns.std() * np.sqrt(252) * 100,
            'sharpe_ratio': returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0,
            'max_drawdown': ((df['close'] / df['close'].cummax()) - 1).min() * 100,
            'average_volume': df['volume'].mean(),
            'price_range': ((df['high'].max() - df['low'].min()) / df['close'].mean()) * 100
        }

        return metrics


async def demo_polygon_client():
    """Polygon 클라이언트 데모"""
    # 실제 API 키 필요
    API_KEY = "YOUR_POLYGON_API_KEY"

    async with PolygonClient(API_KEY, "professional") as client:
        # 1. 주식 데이터
        print("📈 Fetching AAPL stock data...")
        aapl_data = await client.get_aggregates("AAPL", 1, "day", limit=100)
        if aapl_data:
            df = PolygonDataConverter.to_dataframe(aapl_data)
            metrics = PolygonDataConverter.calculate_performance_metrics(df)
            print(f"AAPL metrics: {metrics}")

        # 2. 실시간 호가
        print("💰 Fetching real-time quote...")
        quote = await client.get_real_time_quote("AAPL")
        if quote:
            print(f"AAPL Quote: Bid={quote.bid}, Ask={quote.ask}")

        # 3. 암호화폐 데이터
        print("🪙 Fetching Bitcoin data...")
        btc_data = await client.get_crypto_aggregates("BTCUSD", 1, "day", limit=50)
        if btc_data:
            btc_df = PolygonDataConverter.to_dataframe(btc_data)
            print(f"BTC latest price: ${btc_df['close'].iloc[-1]:,.2f}")

        # 4. 외환 데이터
        print("💱 Fetching forex rates...")
        forex = await client.get_forex_rates("USD", "EUR")
        if forex:
            print(f"USD/EUR rate: {forex.get('mid', 'N/A')}")


if __name__ == "__main__":
    asyncio.run(demo_polygon_client())