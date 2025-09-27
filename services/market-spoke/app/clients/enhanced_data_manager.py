"""
강화된 통합 데이터 매니저
Phase 1 API들을 통합하여 고성능 데이터 서비스 제공
"""

import asyncio
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
from enum import Enum
from concurrent.futures import as_completed
import statistics

from .polygon_client import PolygonClient, PolygonTicker, PolygonDataConverter
from .twelve_data_client import TwelveDataClient, TwelveDataQuote, TwelveDataConverter
from .finnhub_client import FinnhubClient, FinnhubCandle, FinnhubAnalyzer
from .fred_client import FredClient, FredEconomicAnalyzer, FredObservation
from ..exchanges.unified_data_fetcher import UnifiedDataFetcher, DataRequest
from ...shared.utils.data_validator import get_price_validator, ValidationResult

logger = logging.getLogger(__name__)


class DataSource(Enum):
    """데이터 소스"""
    POLYGON = "polygon"
    TWELVE_DATA = "twelve_data"
    FINNHUB = "finnhub"
    FRED = "fred"
    CCXT = "ccxt"


class AssetClass(Enum):
    """자산 클래스"""
    STOCKS = "stocks"
    FOREX = "forex"
    CRYPTO = "crypto"
    COMMODITIES = "commodities"
    BONDS = "bonds"
    ETF = "etf"
    INDICES = "indices"
    ECONOMIC = "economic"


@dataclass
class EnhancedMarketData:
    """강화된 시장 데이터"""
    symbol: str
    asset_class: AssetClass
    data: pd.DataFrame
    sources: List[DataSource]
    validation_result: Optional[ValidationResult] = None
    fundamental_data: Dict[str, Any] = field(default_factory=dict)
    economic_context: Dict[str, Any] = field(default_factory=dict)
    news_sentiment: Dict[str, Any] = field(default_factory=dict)
    technical_signals: Dict[str, Any] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)
    data_quality_score: float = 0.0


@dataclass
class DataSourceConfig:
    """데이터 소스 설정"""
    source: DataSource
    api_key: str
    enabled: bool = True
    priority: int = 1  # 1=highest, 10=lowest
    rate_limit: float = 0.1  # seconds between requests
    timeout: int = 30
    fallback_sources: List[DataSource] = field(default_factory=list)


class EnhancedDataManager:
    """강화된 통합 데이터 매니저"""

    def __init__(self, configs: Dict[DataSource, DataSourceConfig]):
        self.configs = configs
        self.clients: Dict[DataSource, Any] = {}
        self.unified_fetcher: Optional[UnifiedDataFetcher] = None
        self.price_validator = get_price_validator()

        # 성능 통계
        self.performance_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'average_response_time': 0.0,
            'source_performance': {},
            'data_quality_scores': []
        }

        # 데이터 캐시
        self.data_cache: Dict[str, EnhancedMarketData] = {}
        self.economic_cache: Dict[str, Any] = {}

    async def initialize(self):
        """클라이언트 초기화"""
        try:
            # Polygon 클라이언트
            if DataSource.POLYGON in self.configs and self.configs[DataSource.POLYGON].enabled:
                config = self.configs[DataSource.POLYGON]
                self.clients[DataSource.POLYGON] = PolygonClient(
                    config.api_key,
                    "professional"
                )

            # Twelve Data 클라이언트
            if DataSource.TWELVE_DATA in self.configs and self.configs[DataSource.TWELVE_DATA].enabled:
                config = self.configs[DataSource.TWELVE_DATA]
                self.clients[DataSource.TWELVE_DATA] = TwelveDataClient(
                    config.api_key,
                    "pro"
                )

            # Finnhub 클라이언트
            if DataSource.FINNHUB in self.configs and self.configs[DataSource.FINNHUB].enabled:
                config = self.configs[DataSource.FINNHUB]
                self.clients[DataSource.FINNHUB] = FinnhubClient(config.api_key)

            # FRED 클라이언트
            if DataSource.FRED in self.configs and self.configs[DataSource.FRED].enabled:
                config = self.configs[DataSource.FRED]
                self.clients[DataSource.FRED] = FredClient(config.api_key)

            logger.info(f"Initialized {len(self.clients)} data source clients")

        except Exception as e:
            logger.error(f"Error initializing data manager: {e}")
            raise

    async def get_enhanced_market_data(self, symbol: str,
                                     asset_class: AssetClass = AssetClass.STOCKS,
                                     include_fundamentals: bool = True,
                                     include_news: bool = True,
                                     include_economic: bool = True,
                                     timeframe: str = "1day",
                                     limit: int = 1000) -> Optional[EnhancedMarketData]:
        """강화된 시장 데이터 조회 (다중소스 + 펀더멘털 + 뉴스)"""

        start_time = datetime.now()

        try:
            # 1. 기본 가격 데이터 수집 (다중 소스)
            price_data = await self._fetch_multi_source_price_data(
                symbol, asset_class, timeframe, limit
            )

            if price_data.empty:
                logger.warning(f"No price data available for {symbol}")
                return None

            # 2. 펀더멘털 데이터 수집
            fundamental_data = {}
            if include_fundamentals and asset_class == AssetClass.STOCKS:
                fundamental_data = await self._fetch_fundamental_data(symbol)

            # 3. 뉴스 및 감정 분석
            news_sentiment = {}
            if include_news and asset_class == AssetClass.STOCKS:
                news_sentiment = await self._fetch_news_sentiment(symbol)

            # 4. 경제적 맥락 데이터
            economic_context = {}
            if include_economic:
                economic_context = await self._fetch_economic_context(asset_class)

            # 5. 기술적 신호 계산
            technical_signals = await self._calculate_technical_signals(price_data)

            # 6. 데이터 품질 점수 계산
            quality_score = self._calculate_data_quality_score(
                price_data, fundamental_data, news_sentiment
            )

            # 7. 통합 데이터 객체 생성
            enhanced_data = EnhancedMarketData(
                symbol=symbol,
                asset_class=asset_class,
                data=price_data,
                sources=[DataSource.POLYGON, DataSource.TWELVE_DATA, DataSource.FINNHUB],
                fundamental_data=fundamental_data,
                economic_context=economic_context,
                news_sentiment=news_sentiment,
                technical_signals=technical_signals,
                data_quality_score=quality_score
            )

            # 성능 통계 업데이트
            response_time = (datetime.now() - start_time).total_seconds()
            self._update_performance_stats(response_time, quality_score)

            return enhanced_data

        except Exception as e:
            logger.error(f"Error fetching enhanced data for {symbol}: {e}")
            return None

    async def _fetch_multi_source_price_data(self, symbol: str, asset_class: AssetClass,
                                           timeframe: str, limit: int) -> pd.DataFrame:
        """다중 소스에서 가격 데이터 수집"""
        data_sources = []

        # Polygon 데이터
        if DataSource.POLYGON in self.clients:
            try:
                if asset_class == AssetClass.STOCKS:
                    polygon_data = await self.clients[DataSource.POLYGON].get_aggregates(
                        symbol, 1, "day", limit=limit
                    )
                elif asset_class == AssetClass.CRYPTO:
                    polygon_data = await self.clients[DataSource.POLYGON].get_crypto_aggregates(
                        symbol, 1, "day", limit=limit
                    )
                else:
                    polygon_data = []

                if polygon_data:
                    polygon_df = PolygonDataConverter.to_dataframe(polygon_data)
                    polygon_df['source'] = 'polygon'
                    data_sources.append(polygon_df)

            except Exception as e:
                logger.warning(f"Polygon data fetch failed for {symbol}: {e}")

        # Twelve Data
        if DataSource.TWELVE_DATA in self.clients:
            try:
                twelve_data = await self.clients[DataSource.TWELVE_DATA].get_time_series(
                    symbol, timeframe, limit
                )
                if twelve_data:
                    twelve_df = TwelveDataConverter.to_dataframe(twelve_data)
                    twelve_df['source'] = 'twelve_data'
                    data_sources.append(twelve_df)

            except Exception as e:
                logger.warning(f"Twelve Data fetch failed for {symbol}: {e}")

        # Finnhub 데이터
        if DataSource.FINNHUB in self.clients:
            try:
                # 시간 범위 계산
                to_timestamp = int(datetime.now().timestamp())
                from_timestamp = int((datetime.now() - timedelta(days=limit)).timestamp())

                finnhub_data = await self.clients[DataSource.FINNHUB].get_candles(
                    symbol, "D", from_timestamp, to_timestamp
                )
                if finnhub_data:
                    finnhub_df = FinnhubAnalyzer.to_dataframe(finnhub_data)
                    finnhub_df['source'] = 'finnhub'
                    data_sources.append(finnhub_df)

            except Exception as e:
                logger.warning(f"Finnhub data fetch failed for {symbol}: {e}")

        # 데이터 통합 및 검증
        if not data_sources:
            return pd.DataFrame()

        # 가장 완전한 데이터셋을 기준으로 사용
        primary_df = max(data_sources, key=len)

        # 다른 소스들과 가격 검증
        if len(data_sources) > 1:
            validation_data = {}
            for df in data_sources:
                if not df.empty and 'close' in df.columns:
                    source_name = df['source'].iloc[0]
                    validation_data[source_name] = df['close'].iloc[-1]

            # 가격 검증 수행
            if len(validation_data) >= 2:
                try:
                    validation_result = await self.price_validator.validate_crypto_price(
                        symbol, validation_data
                    )
                    primary_df['validation_quality'] = validation_result.quality.value
                    primary_df['confidence_score'] = validation_result.confidence_score
                except Exception as e:
                    logger.warning(f"Price validation failed: {e}")

        return primary_df.drop('source', axis=1, errors='ignore')

    async def _fetch_fundamental_data(self, symbol: str) -> Dict[str, Any]:
        """펀더멘털 데이터 수집"""
        fundamental_data = {}

        if DataSource.FINNHUB in self.clients:
            try:
                client = self.clients[DataSource.FINNHUB]

                # 기업 프로필
                profile = await client.get_company_profile(symbol)
                if profile:
                    fundamental_data['profile'] = {
                        'name': profile.name,
                        'industry': profile.industry,
                        'market_cap': profile.market_cap,
                        'country': profile.country
                    }

                # 기본 재무 지표
                basic_financials = await client.get_basic_financials(symbol)
                if basic_financials:
                    fundamental_data['metrics'] = basic_financials

                # 재무제표
                financials = await client.get_financials_reported(symbol)
                if financials:
                    analysis = FinnhubAnalyzer.analyze_fundamental_strength(financials)
                    fundamental_data['strength_analysis'] = analysis

                # 애널리스트 추천
                recommendations = await client.get_recommendation_trends(symbol)
                if recommendations:
                    fundamental_data['recommendations'] = recommendations[:5]  # 최근 5개

            except Exception as e:
                logger.warning(f"Fundamental data fetch failed for {symbol}: {e}")

        return fundamental_data

    async def _fetch_news_sentiment(self, symbol: str) -> Dict[str, Any]:
        """뉴스 및 감정 분석"""
        news_sentiment = {}

        if DataSource.FINNHUB in self.clients:
            try:
                client = self.clients[DataSource.FINNHUB]

                # 기업 뉴스
                news = await client.get_company_news(symbol)
                if news:
                    sentiment_analysis = FinnhubAnalyzer.sentiment_analysis(news)
                    news_sentiment.update(sentiment_analysis)
                    news_sentiment['recent_headlines'] = [
                        {'headline': n.headline, 'date': n.datetime.isoformat(), 'source': n.source}
                        for n in news[:10]
                    ]

            except Exception as e:
                logger.warning(f"News sentiment fetch failed for {symbol}: {e}")

        return news_sentiment

    async def _fetch_economic_context(self, asset_class: AssetClass) -> Dict[str, Any]:
        """경제적 맥락 데이터 수집"""
        economic_context = {}

        if DataSource.FRED in self.clients:
            try:
                fred_client = self.clients[DataSource.FRED]
                analyzer = FredEconomicAnalyzer(fred_client)

                # 주요 경제 지표
                indicators = await analyzer.get_key_economic_indicators(lookback_months=6)
                if indicators:
                    economic_context['key_indicators'] = {
                        name: {
                            'current_value': ind.current_value,
                            'change': ind.change,
                            'percent_change': ind.percent_change,
                            'trend': ind.trend
                        }
                        for name, ind in indicators.items()
                    }

                # 경기침체 확률
                recession_prob = await analyzer.calculate_recession_probability()
                economic_context['recession_probability'] = recession_prob

                # 수익률 곡선 분석
                yield_analysis = await analyzer.get_yield_curve_analysis()
                if yield_analysis:
                    economic_context['yield_curve'] = yield_analysis

            except Exception as e:
                logger.warning(f"Economic context fetch failed: {e}")

        return economic_context

    async def _calculate_technical_signals(self, df: pd.DataFrame) -> Dict[str, Any]:
        """기술적 신호 계산"""
        if df.empty or 'close' in df.columns:
            return {}

        try:
            signals = {}

            # 이동평균
            df['sma_20'] = df['close'].rolling(window=20).mean()
            df['sma_50'] = df['close'].rolling(window=50).mean()
            df['ema_12'] = df['close'].ewm(span=12).mean()
            df['ema_26'] = df['close'].ewm(span=26).mean()

            # MACD
            df['macd'] = df['ema_12'] - df['ema_26']
            df['macd_signal'] = df['macd'].ewm(span=9).mean()

            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))

            # 현재 신호들
            latest = df.iloc[-1]
            signals = {
                'price_vs_sma20': 'bullish' if latest['close'] > latest['sma_20'] else 'bearish',
                'sma_cross': 'bullish' if latest['sma_20'] > latest['sma_50'] else 'bearish',
                'macd_signal': 'bullish' if latest['macd'] > latest['macd_signal'] else 'bearish',
                'rsi_level': 'overbought' if latest['rsi'] > 70 else 'oversold' if latest['rsi'] < 30 else 'neutral',
                'current_rsi': latest['rsi'],
                'trend_strength': abs(latest['close'] - latest['sma_20']) / latest['sma_20'] * 100
            }

            return signals

        except Exception as e:
            logger.warning(f"Technical analysis failed: {e}")
            return {}

    def _calculate_data_quality_score(self, price_data: pd.DataFrame,
                                    fundamental_data: Dict, news_sentiment: Dict) -> float:
        """데이터 품질 점수 계산 (0-100)"""
        score = 0.0

        # 가격 데이터 품질 (40점)
        if not price_data.empty:
            score += 20  # 기본 점수

            # 데이터 완성도
            completeness = (len(price_data) / 1000) * 10  # 1000개 기준
            score += min(completeness, 10)

            # 검증 품질
            if 'validation_quality' in price_data.columns:
                quality_map = {'excellent': 10, 'good': 7, 'fair': 4, 'poor': 1}
                score += quality_map.get(price_data['validation_quality'].iloc[-1], 0)

        # 펀더멘털 데이터 품질 (30점)
        if fundamental_data:
            score += 10  # 기본 점수
            if 'profile' in fundamental_data:
                score += 5
            if 'metrics' in fundamental_data:
                score += 5
            if 'strength_analysis' in fundamental_data:
                score += 5
            if 'recommendations' in fundamental_data:
                score += 5

        # 뉴스/감정 데이터 품질 (20점)
        if news_sentiment:
            score += 10  # 기본 점수
            if 'sentiment_score' in news_sentiment:
                score += 5
            if 'recent_headlines' in news_sentiment:
                score += 5

        # 실시간성 (10점)
        if hasattr(self, 'last_updated'):
            age_minutes = (datetime.now() - self.last_updated).total_seconds() / 60
            if age_minutes < 5:
                score += 10
            elif age_minutes < 15:
                score += 7
            elif age_minutes < 60:
                score += 4
            else:
                score += 1

        return min(score, 100.0)

    def _update_performance_stats(self, response_time: float, quality_score: float):
        """성능 통계 업데이트"""
        self.performance_stats['total_requests'] += 1
        self.performance_stats['successful_requests'] += 1

        # 평균 응답시간 업데이트
        total = self.performance_stats['total_requests']
        current_avg = self.performance_stats['average_response_time']
        self.performance_stats['average_response_time'] = (
            (current_avg * (total - 1) + response_time) / total
        )

        # 품질 점수 기록
        self.performance_stats['data_quality_scores'].append(quality_score)
        if len(self.performance_stats['data_quality_scores']) > 1000:
            self.performance_stats['data_quality_scores'] = \
                self.performance_stats['data_quality_scores'][-1000:]

    async def get_market_overview(self, symbols: List[str] = None,
                                asset_classes: List[AssetClass] = None) -> Dict[str, Any]:
        """시장 개요 생성"""
        if not symbols:
            symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA"]  # 기본 심볼들

        if not asset_classes:
            asset_classes = [AssetClass.STOCKS]

        overview = {
            'timestamp': datetime.now().isoformat(),
            'markets': {},
            'economic_summary': {},
            'performance_summary': {}
        }

        # 각 심볼의 데이터 수집
        tasks = []
        for symbol in symbols:
            for asset_class in asset_classes:
                task = self.get_enhanced_market_data(
                    symbol, asset_class,
                    include_fundamentals=False,
                    include_news=False,
                    limit=50
                )
                tasks.append((symbol, task))

        # 결과 수집
        for symbol, task in tasks:
            try:
                data = await task
                if data:
                    overview['markets'][symbol] = {
                        'current_price': data.data['close'].iloc[-1] if not data.data.empty else 0,
                        'change_percent': self._calculate_daily_change(data.data),
                        'quality_score': data.data_quality_score,
                        'technical_signal': data.technical_signals.get('price_vs_sma20', 'neutral')
                    }
            except Exception as e:
                logger.warning(f"Failed to get overview data for {symbol}: {e}")

        # 경제 요약
        if DataSource.FRED in self.clients:
            try:
                fred_client = self.clients[DataSource.FRED]
                analyzer = FredEconomicAnalyzer(fred_client)

                recession_prob = await analyzer.calculate_recession_probability()
                overview['economic_summary']['recession_probability'] = recession_prob

            except Exception as e:
                logger.warning(f"Economic summary failed: {e}")

        # 성능 요약
        overview['performance_summary'] = {
            'total_requests': self.performance_stats['total_requests'],
            'average_response_time': self.performance_stats['average_response_time'],
            'average_quality_score': statistics.mean(self.performance_stats['data_quality_scores'])
                                   if self.performance_stats['data_quality_scores'] else 0
        }

        return overview

    def _calculate_daily_change(self, df: pd.DataFrame) -> float:
        """일일 변화율 계산"""
        if df.empty or len(df) < 2:
            return 0.0

        current = df['close'].iloc[-1]
        previous = df['close'].iloc[-2]
        return ((current - previous) / previous) * 100

    async def get_performance_report(self) -> Dict[str, Any]:
        """성능 리포트 생성"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'overall_performance': self.performance_stats.copy(),
            'data_sources_status': {},
            'recommendations': []
        }

        # 각 데이터 소스 상태 확인
        for source, client in self.clients.items():
            try:
                # 간단한 테스트 호출
                status = 'online'
                if source == DataSource.POLYGON:
                    await client.get_market_status()
                elif source == DataSource.TWELVE_DATA:
                    await client.get_real_time_price("AAPL")
                elif source == DataSource.FINNHUB:
                    await client.get_quote("AAPL")
                # FRED는 상태 확인 API가 없으므로 기본적으로 온라인으로 가정

                report['data_sources_status'][source.value] = {
                    'status': status,
                    'last_check': datetime.now().isoformat()
                }

            except Exception as e:
                report['data_sources_status'][source.value] = {
                    'status': 'error',
                    'error': str(e),
                    'last_check': datetime.now().isoformat()
                }

        # 성능 개선 권고사항
        avg_quality = statistics.mean(self.performance_stats['data_quality_scores']) \
                     if self.performance_stats['data_quality_scores'] else 0

        if avg_quality < 70:
            report['recommendations'].append("데이터 품질이 낮습니다. 추가 데이터 소스를 고려하세요.")

        if self.performance_stats['average_response_time'] > 2.0:
            report['recommendations'].append("응답 시간이 느립니다. 캐싱 전략을 검토하세요.")

        return report

    async def shutdown(self):
        """클라이언트 종료"""
        for client in self.clients.values():
            try:
                if hasattr(client, '__aexit__'):
                    await client.__aexit__(None, None, None)
            except Exception as e:
                logger.error(f"Error shutting down client: {e}")

        logger.info("Enhanced Data Manager shutdown complete")


async def demo_enhanced_data_manager():
    """강화된 데이터 매니저 데모"""
    # 설정 (실제 API 키 필요)
    configs = {
        DataSource.POLYGON: DataSourceConfig(
            source=DataSource.POLYGON,
            api_key="YOUR_POLYGON_API_KEY",
            priority=1
        ),
        DataSource.TWELVE_DATA: DataSourceConfig(
            source=DataSource.TWELVE_DATA,
            api_key="YOUR_TWELVE_DATA_API_KEY",
            priority=2
        ),
        DataSource.FINNHUB: DataSourceConfig(
            source=DataSource.FINNHUB,
            api_key="YOUR_FINNHUB_API_KEY",
            priority=3
        ),
        DataSource.FRED: DataSourceConfig(
            source=DataSource.FRED,
            api_key="YOUR_FRED_API_KEY",
            priority=4
        )
    }

    manager = EnhancedDataManager(configs)

    try:
        await manager.initialize()

        # 1. 강화된 시장 데이터 조회
        print("📊 Fetching enhanced market data for AAPL...")
        aapl_data = await manager.get_enhanced_market_data("AAPL", AssetClass.STOCKS)

        if aapl_data:
            print(f"✅ Data quality score: {aapl_data.data_quality_score:.1f}/100")
            print(f"📈 Current price: ${aapl_data.data['close'].iloc[-1]:.2f}")
            print(f"🎯 Technical signal: {aapl_data.technical_signals.get('price_vs_sma20', 'N/A')}")

            if aapl_data.fundamental_data:
                print(f"🏢 Company: {aapl_data.fundamental_data.get('profile', {}).get('name', 'N/A')}")

            if aapl_data.news_sentiment:
                sentiment = aapl_data.news_sentiment.get('sentiment_score', 0)
                print(f"📰 News sentiment: {sentiment:.2f}")

        # 2. 시장 개요
        print("\n🌍 Market overview...")
        overview = await manager.get_market_overview()
        for symbol, data in overview['markets'].items():
            print(f"{symbol}: ${data['current_price']:.2f} ({data['change_percent']:+.2f}%)")

        # 3. 성능 리포트
        print("\n📋 Performance report...")
        report = await manager.get_performance_report()
        print(f"Total requests: {report['overall_performance']['total_requests']}")
        print(f"Avg response time: {report['overall_performance']['average_response_time']:.2f}s")

    finally:
        await manager.shutdown()


if __name__ == "__main__":
    asyncio.run(demo_enhanced_data_manager())