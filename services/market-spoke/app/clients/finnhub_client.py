"""
Finnhub API 클라이언트
펀더멘털 분석 및 시장 뉴스 데이터 제공
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


class FinnhubResolution(Enum):
    """Finnhub 해상도"""
    MIN_1 = "1"
    MIN_5 = "5"
    MIN_15 = "15"
    MIN_30 = "30"
    MIN_60 = "60"
    DAY_1 = "D"
    WEEK_1 = "W"
    MONTH_1 = "M"


@dataclass
class FinnhubCandle:
    """Finnhub 캔들 데이터"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    status: str = "ok"


@dataclass
class FinnhubQuote:
    """Finnhub 실시간 시세"""
    symbol: str
    current_price: float
    change: float
    percent_change: float
    high: float
    low: float
    open: float
    previous_close: float
    timestamp: datetime


@dataclass
class FinnhubCompanyProfile:
    """기업 프로필"""
    symbol: str
    name: str
    country: str
    currency: str
    exchange: str
    industry: str
    logo: str
    market_cap: float
    share_outstanding: float
    website: str


@dataclass
class FinnhubFinancials:
    """재무제표 데이터"""
    symbol: str
    period: str
    year: int
    quarter: Optional[int]
    revenue: Optional[float]
    earnings: Optional[float]
    eps: Optional[float]
    debt: Optional[float]
    assets: Optional[float]
    equity: Optional[float]


@dataclass
class FinnhubNews:
    """뉴스 데이터"""
    id: str
    headline: str
    summary: str
    source: str
    url: str
    image: str
    datetime: datetime
    related_symbols: List[str]
    sentiment: Optional[Dict[str, float]] = None


@dataclass
class FinnhubEarnings:
    """실적 발표 일정"""
    symbol: str
    date: datetime
    eps_estimate: Optional[float]
    eps_actual: Optional[float]
    revenue_estimate: Optional[float]
    revenue_actual: Optional[float]
    surprise_percent: Optional[float]


class FinnhubClient:
    """Finnhub API 클라이언트"""

    BASE_URL = "https://finnhub.io/api/v1"
    WS_URL = "wss://ws.finnhub.io"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None
        self.ws_connection: Optional[websockets.WebSocketServerProtocol] = None
        self.subscriptions: Dict[str, Any] = {}

        # Free tier: 60 calls/minute
        self.request_delay = 1.0

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
        params["token"] = self.api_key

        try:
            await asyncio.sleep(self.request_delay)  # Rate limiting

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"Finnhub API error {response.status}: {error_text}")

        except Exception as e:
            logger.error(f"Finnhub API request failed: {e}")
            raise

    async def get_candles(self, symbol: str, resolution: str = "D",
                         from_timestamp: int = None, to_timestamp: int = None) -> List[FinnhubCandle]:
        """캔들 데이터 조회"""
        if not from_timestamp:
            from_timestamp = int((datetime.now() - timedelta(days=365)).timestamp())
        if not to_timestamp:
            to_timestamp = int(datetime.now().timestamp())

        endpoint = "/stock/candle"
        params = {
            "symbol": symbol,
            "resolution": resolution,
            "from": from_timestamp,
            "to": to_timestamp
        }

        try:
            response = await self._make_request(endpoint, params)

            if response.get("s") != "ok":
                logger.warning(f"No data available for {symbol}")
                return []

            candles = []
            timestamps = response.get("t", [])
            opens = response.get("o", [])
            highs = response.get("h", [])
            lows = response.get("l", [])
            closes = response.get("c", [])
            volumes = response.get("v", [])

            for i in range(len(timestamps)):
                candle = FinnhubCandle(
                    timestamp=datetime.fromtimestamp(timestamps[i]),
                    open=opens[i],
                    high=highs[i],
                    low=lows[i],
                    close=closes[i],
                    volume=int(volumes[i]),
                    status=response["s"]
                )
                candles.append(candle)

            return candles

        except Exception as e:
            logger.error(f"Error fetching candles for {symbol}: {e}")
            return []

    async def get_quote(self, symbol: str) -> Optional[FinnhubQuote]:
        """실시간 시세 조회"""
        endpoint = "/quote"
        params = {"symbol": symbol}

        try:
            response = await self._make_request(endpoint, params)

            return FinnhubQuote(
                symbol=symbol,
                current_price=response["c"],
                change=response["d"],
                percent_change=response["dp"],
                high=response["h"],
                low=response["l"],
                open=response["o"],
                previous_close=response["pc"],
                timestamp=datetime.fromtimestamp(response["t"])
            )

        except Exception as e:
            logger.error(f"Error fetching quote for {symbol}: {e}")
            return None

    async def get_company_profile(self, symbol: str) -> Optional[FinnhubCompanyProfile]:
        """기업 프로필 조회"""
        endpoint = "/stock/profile2"
        params = {"symbol": symbol}

        try:
            response = await self._make_request(endpoint, params)

            if not response:
                return None

            return FinnhubCompanyProfile(
                symbol=symbol,
                name=response.get("name", ""),
                country=response.get("country", ""),
                currency=response.get("currency", ""),
                exchange=response.get("exchange", ""),
                industry=response.get("finnhubIndustry", ""),
                logo=response.get("logo", ""),
                market_cap=response.get("marketCapitalization", 0.0),
                share_outstanding=response.get("shareOutstanding", 0.0),
                website=response.get("weburl", "")
            )

        except Exception as e:
            logger.error(f"Error fetching company profile for {symbol}: {e}")
            return None

    async def get_basic_financials(self, symbol: str, metric: str = "all") -> Dict[str, Any]:
        """기본 재무 지표 조회"""
        endpoint = "/stock/metric"
        params = {"symbol": symbol, "metric": metric}

        try:
            response = await self._make_request(endpoint, params)
            return response.get("metric", {})

        except Exception as e:
            logger.error(f"Error fetching basic financials for {symbol}: {e}")
            return {}

    async def get_financials_reported(self, symbol: str,
                                    freq: str = "annual") -> List[FinnhubFinancials]:
        """보고된 재무제표 조회"""
        endpoint = "/stock/financials-reported"
        params = {"symbol": symbol, "freq": freq}

        try:
            response = await self._make_request(endpoint, params)
            data = response.get("data", [])

            financials = []
            for item in data:
                report = item.get("report", {})
                ic = report.get("ic", [])  # Income Statement
                bs = report.get("bs", [])  # Balance Sheet

                # 주요 지표 추출
                revenue = None
                earnings = None
                eps = None
                debt = None
                assets = None
                equity = None

                for entry in ic:
                    if entry.get("concept") == "Revenues":
                        revenue = entry.get("value")
                    elif entry.get("concept") == "NetIncomeLoss":
                        earnings = entry.get("value")

                for entry in bs:
                    if entry.get("concept") == "Assets":
                        assets = entry.get("value")
                    elif entry.get("concept") == "Liabilities":
                        debt = entry.get("value")
                    elif entry.get("concept") == "StockholdersEquity":
                        equity = entry.get("value")

                financial = FinnhubFinancials(
                    symbol=symbol,
                    period=item.get("period"),
                    year=item.get("year"),
                    quarter=item.get("quarter"),
                    revenue=revenue,
                    earnings=earnings,
                    eps=eps,
                    debt=debt,
                    assets=assets,
                    equity=equity
                )
                financials.append(financial)

            return financials

        except Exception as e:
            logger.error(f"Error fetching reported financials for {symbol}: {e}")
            return []

    async def get_company_news(self, symbol: str, from_date: str = None,
                             to_date: str = None) -> List[FinnhubNews]:
        """기업 뉴스 조회"""
        if not from_date:
            from_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not to_date:
            to_date = datetime.now().strftime("%Y-%m-%d")

        endpoint = "/company-news"
        params = {
            "symbol": symbol,
            "from": from_date,
            "to": to_date
        }

        try:
            response = await self._make_request(endpoint, params)

            news_list = []
            for item in response:
                news = FinnhubNews(
                    id=str(item.get("id", "")),
                    headline=item.get("headline", ""),
                    summary=item.get("summary", ""),
                    source=item.get("source", ""),
                    url=item.get("url", ""),
                    image=item.get("image", ""),
                    datetime=datetime.fromtimestamp(item.get("datetime", 0)),
                    related_symbols=[item.get("symbol", symbol)]
                )
                news_list.append(news)

            return news_list

        except Exception as e:
            logger.error(f"Error fetching news for {symbol}: {e}")
            return []

    async def get_market_news(self, category: str = "general",
                            min_id: int = 0) -> List[FinnhubNews]:
        """일반 시장 뉴스 조회"""
        endpoint = "/news"
        params = {"category": category, "minId": min_id}

        try:
            response = await self._make_request(endpoint, params)

            news_list = []
            for item in response:
                news = FinnhubNews(
                    id=str(item.get("id", "")),
                    headline=item.get("headline", ""),
                    summary=item.get("summary", ""),
                    source=item.get("source", ""),
                    url=item.get("url", ""),
                    image=item.get("image", ""),
                    datetime=datetime.fromtimestamp(item.get("datetime", 0)),
                    related_symbols=item.get("related", [])
                )
                news_list.append(news)

            return news_list

        except Exception as e:
            logger.error(f"Error fetching market news: {e}")
            return []

    async def get_earnings_calendar(self, from_date: str = None,
                                  to_date: str = None,
                                  symbol: str = None) -> List[FinnhubEarnings]:
        """실적 발표 일정 조회"""
        if not from_date:
            from_date = datetime.now().strftime("%Y-%m-%d")
        if not to_date:
            to_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

        endpoint = "/calendar/earnings"
        params = {"from": from_date, "to": to_date}

        if symbol:
            params["symbol"] = symbol

        try:
            response = await self._make_request(endpoint, params)

            earnings_list = []
            for item in response.get("earningsCalendar", []):
                earnings = FinnhubEarnings(
                    symbol=item.get("symbol", ""),
                    date=datetime.fromisoformat(item.get("date", "")),
                    eps_estimate=item.get("epsEstimate"),
                    eps_actual=item.get("epsActual"),
                    revenue_estimate=item.get("revenueEstimate"),
                    revenue_actual=item.get("revenueActual"),
                    surprise_percent=item.get("surprisePercent")
                )
                earnings_list.append(earnings)

            return earnings_list

        except Exception as e:
            logger.error(f"Error fetching earnings calendar: {e}")
            return []

    async def get_recommendation_trends(self, symbol: str) -> List[Dict[str, Any]]:
        """애널리스트 추천 동향"""
        endpoint = "/stock/recommendation"
        params = {"symbol": symbol}

        try:
            response = await self._make_request(endpoint, params)
            return response

        except Exception as e:
            logger.error(f"Error fetching recommendations for {symbol}: {e}")
            return []

    async def get_price_target(self, symbol: str) -> Dict[str, Any]:
        """가격 목표 조회"""
        endpoint = "/stock/price-target"
        params = {"symbol": symbol}

        try:
            response = await self._make_request(endpoint, params)
            return response

        except Exception as e:
            logger.error(f"Error fetching price target for {symbol}: {e}")
            return {}

    async def get_insider_transactions(self, symbol: str,
                                     from_date: str = None,
                                     to_date: str = None) -> List[Dict[str, Any]]:
        """내부자 거래 조회"""
        endpoint = "/stock/insider-transactions"
        params = {"symbol": symbol}

        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date

        try:
            response = await self._make_request(endpoint, params)
            return response.get("data", [])

        except Exception as e:
            logger.error(f"Error fetching insider transactions for {symbol}: {e}")
            return []

    async def start_websocket_stream(self, symbols: List[str], callback):
        """WebSocket 실시간 스트림"""
        try:
            uri = f"{self.WS_URL}?token={self.api_key}"
            self.ws_connection = await websockets.connect(uri)

            # 심볼 구독
            for symbol in symbols:
                subscribe_msg = {"type": "subscribe", "symbol": symbol}
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


class FinnhubAnalyzer:
    """Finnhub 데이터 분석 도구"""

    @staticmethod
    def to_dataframe(candles: List[FinnhubCandle]) -> pd.DataFrame:
        """캔들 데이터를 DataFrame으로 변환"""
        if not candles:
            return pd.DataFrame()

        data = []
        for candle in candles:
            data.append({
                'timestamp': candle.timestamp,
                'open': candle.open,
                'high': candle.high,
                'low': candle.low,
                'close': candle.close,
                'volume': candle.volume
            })

        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        return df

    @staticmethod
    def analyze_fundamental_strength(financials: List[FinnhubFinancials]) -> Dict[str, Any]:
        """펀더멘털 강도 분석"""
        if not financials:
            return {}

        # 최신 재무 데이터
        latest = financials[0]

        metrics = {
            'revenue_growth': 0.0,
            'earnings_growth': 0.0,
            'debt_to_equity': 0.0,
            'roe': 0.0,  # Return on Equity
            'fundamental_score': 0.0
        }

        # 성장률 계산 (최근 2년간)
        if len(financials) >= 2:
            prev = financials[1]
            if latest.revenue and prev.revenue and prev.revenue != 0:
                metrics['revenue_growth'] = ((latest.revenue - prev.revenue) / prev.revenue) * 100

            if latest.earnings and prev.earnings and prev.earnings != 0:
                metrics['earnings_growth'] = ((latest.earnings - prev.earnings) / prev.earnings) * 100

        # 부채비율
        if latest.debt and latest.equity and latest.equity != 0:
            metrics['debt_to_equity'] = latest.debt / latest.equity

        # ROE
        if latest.earnings and latest.equity and latest.equity != 0:
            metrics['roe'] = (latest.earnings / latest.equity) * 100

        # 종합 펀더멘털 점수 (0-100)
        score = 50  # 기본 점수

        if metrics['revenue_growth'] > 0:
            score += min(metrics['revenue_growth'], 20)

        if metrics['earnings_growth'] > 0:
            score += min(metrics['earnings_growth'], 20)

        if metrics['debt_to_equity'] < 1.0:
            score += 10

        if metrics['roe'] > 10:
            score += 10

        metrics['fundamental_score'] = min(max(score, 0), 100)

        return metrics

    @staticmethod
    def sentiment_analysis(news_list: List[FinnhubNews]) -> Dict[str, Any]:
        """뉴스 감정 분석"""
        if not news_list:
            return {'sentiment_score': 0.0, 'news_count': 0}

        # 간단한 키워드 기반 감정 분석
        positive_keywords = ['growth', 'profit', 'gain', 'increase', 'strong', 'beat', 'exceed']
        negative_keywords = ['loss', 'decline', 'fall', 'weak', 'miss', 'concern', 'risk']

        sentiment_scores = []
        for news in news_list:
            text = (news.headline + " " + news.summary).lower()
            positive_count = sum(1 for word in positive_keywords if word in text)
            negative_count = sum(1 for word in negative_keywords if word in text)

            if positive_count + negative_count > 0:
                score = (positive_count - negative_count) / (positive_count + negative_count)
            else:
                score = 0.0

            sentiment_scores.append(score)

        avg_sentiment = np.mean(sentiment_scores) if sentiment_scores else 0.0

        return {
            'sentiment_score': avg_sentiment,
            'news_count': len(news_list),
            'positive_ratio': sum(1 for s in sentiment_scores if s > 0) / len(sentiment_scores) if sentiment_scores else 0
        }


async def demo_finnhub_client():
    """Finnhub 클라이언트 데모"""
    # 실제 API 키 필요
    API_KEY = "YOUR_FINNHUB_API_KEY"

    async with FinnhubClient(API_KEY) as client:
        symbol = "AAPL"

        # 1. 기업 프로필
        print(f"📋 Company profile for {symbol}...")
        profile = await client.get_company_profile(symbol)
        if profile:
            print(f"Name: {profile.name}, Industry: {profile.industry}")

        # 2. 캔들 데이터
        print(f"📈 Fetching candles for {symbol}...")
        candles = await client.get_candles(symbol, "D")
        if candles:
            df = FinnhubAnalyzer.to_dataframe(candles)
            print(f"Latest close: ${df['close'].iloc[-1]:.2f}")

        # 3. 재무 데이터
        print(f"💰 Fetching financials for {symbol}...")
        financials = await client.get_financials_reported(symbol)
        if financials:
            analysis = FinnhubAnalyzer.analyze_fundamental_strength(financials)
            print(f"Fundamental score: {analysis['fundamental_score']:.1f}")

        # 4. 뉴스 분석
        print(f"📰 Analyzing news for {symbol}...")
        news = await client.get_company_news(symbol)
        if news:
            sentiment = FinnhubAnalyzer.sentiment_analysis(news)
            print(f"Sentiment score: {sentiment['sentiment_score']:.2f}")


if __name__ == "__main__":
    asyncio.run(demo_finnhub_client())