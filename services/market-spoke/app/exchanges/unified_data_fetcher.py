"""
통합 데이터 페처
여러 거래소에서 동시에 데이터를 수집하고 검증하는 시스템
"""

import asyncio
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import statistics
import logging
from concurrent.futures import as_completed

from .ccxt_manager import CCXTManager, TickerData, OHLCVData
from ..indicators import IndicatorBatch, BaseIndicator
from ...shared.utils.data_validator import get_price_validator, ValidationResult, DataPoint


logger = logging.getLogger(__name__)


@dataclass
class DataRequest:
    """데이터 요청 정의"""
    symbol: str
    timeframe: str = '1d'
    since: Optional[datetime] = None
    limit: int = 100
    exchanges: Optional[List[str]] = None
    require_validation: bool = True
    max_age_minutes: int = 60


@dataclass
class UnifiedMarketData:
    """통합 시장 데이터"""
    symbol: str
    timeframe: str
    data: pd.DataFrame
    sources: List[str]
    validation_result: Optional[ValidationResult] = None
    last_updated: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class UnifiedDataFetcher:
    """통합 데이터 페처 - 다중 거래소 데이터 수집"""

    def __init__(self, ccxt_manager: CCXTManager):
        self.ccxt_manager = ccxt_manager
        self.price_validator = get_price_validator()
        self.data_cache: Dict[str, UnifiedMarketData] = {}
        self.fetch_stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'validation_failures': 0,
            'source_failures': {}
        }

    async def fetch_current_prices(self, symbols: List[str],
                                 exchanges: Optional[List[str]] = None) -> Dict[str, ValidationResult]:
        """현재 가격 데이터 다중소스 수집 및 검증"""
        if exchanges is None:
            exchanges = self.ccxt_manager.get_active_exchanges()

        results = {}

        for symbol in symbols:
            try:
                # 다중 거래소에서 동시 데이터 수집
                price_data = await self._fetch_prices_from_exchanges(symbol, exchanges)

                if len(price_data) >= 2:
                    # 다중소스 검증
                    validation_result = await self.price_validator.validate_crypto_price(
                        symbol, price_data
                    )
                    results[symbol] = validation_result
                else:
                    # 단일 소스인 경우 경고와 함께 결과 반환
                    if price_data:
                        source, price = next(iter(price_data.items()))
                        results[symbol] = ValidationResult(
                            consensus_value=price,
                            quality="insufficient",
                            confidence_score=0.3,
                            source_count=1,
                            warnings=[f"Only one source available: {source}"]
                        )

                self.fetch_stats['total_requests'] += 1

            except Exception as e:
                logger.error(f"Error fetching price for {symbol}: {e}")

        return results

    async def fetch_historical_data(self, request: DataRequest) -> UnifiedMarketData:
        """과거 데이터 다중소스 수집"""
        cache_key = f"{request.symbol}:{request.timeframe}:{request.since}:{request.limit}"

        # 캐시 확인
        if cache_key in self.data_cache:
            cached_data = self.data_cache[cache_key]
            age_minutes = (datetime.now() - cached_data.last_updated).total_seconds() / 60

            if age_minutes < request.max_age_minutes:
                self.fetch_stats['cache_hits'] += 1
                return cached_data

        # 활성 거래소 목록
        exchanges = request.exchanges or self.ccxt_manager.get_active_exchanges()

        # 다중 거래소에서 데이터 수집
        ohlcv_data = await self._fetch_ohlcv_from_exchanges(
            request.symbol, request.timeframe, exchanges, request.since, request.limit
        )

        # 데이터 통합 및 검증
        unified_data = await self._unify_ohlcv_data(ohlcv_data, request)

        # 캐시에 저장
        self.data_cache[cache_key] = unified_data

        # 캐시 크기 관리
        if len(self.data_cache) > 100:
            oldest_key = min(self.data_cache.keys(),
                           key=lambda k: self.data_cache[k].last_updated)
            del self.data_cache[oldest_key]

        return unified_data

    async def fetch_with_indicators(self, request: DataRequest,
                                  indicators: List[BaseIndicator]) -> Tuple[UnifiedMarketData, Dict[str, Any]]:
        """데이터 수집 + 기술지표 계산"""
        # 1. 기본 데이터 수집
        market_data = await self.fetch_historical_data(request)

        # 2. 기술지표 배치 계산
        if not market_data.data.empty:
            indicator_batch = IndicatorBatch(indicators)
            indicator_results = indicator_batch.calculate_all(market_data.data)
        else:
            indicator_results = {}

        return market_data, indicator_results

    async def get_market_overview(self, base_currency: str = 'USDT',
                                limit: int = 20) -> Dict[str, Any]:
        """시장 개요 데이터 수집"""
        # 주요 거래소에서 인기 심볼 수집
        exchanges = ['binance', 'coinbase', 'kraken']
        all_symbols = set()

        for exchange_id in exchanges:
            if exchange_id in self.ccxt_manager.exchanges:
                symbols = await self.ccxt_manager.get_supported_symbols(exchange_id, None)
                # base_currency와 페어인 심볼만 필터링
                filtered_symbols = [s for s in symbols if s.endswith(f'/{base_currency}')]
                all_symbols.update(filtered_symbols[:limit])

        # 현재 가격 수집
        symbol_list = list(all_symbols)[:limit]
        price_results = await self.fetch_current_prices(symbol_list, exchanges)

        # 결과 정리
        overview = {
            'timestamp': datetime.now().isoformat(),
            'base_currency': base_currency,
            'markets': {}
        }

        for symbol, validation_result in price_results.items():
            overview['markets'][symbol] = {
                'price': validation_result.consensus_value,
                'quality': validation_result.quality.value,
                'confidence': validation_result.confidence_score,
                'sources': validation_result.source_count
            }

        return overview

    async def _fetch_prices_from_exchanges(self, symbol: str,
                                         exchanges: List[str]) -> Dict[str, float]:
        """다중 거래소에서 가격 데이터 수집"""
        tasks = []

        for exchange_id in exchanges:
            if exchange_id in self.ccxt_manager.exchanges:
                task = self._fetch_single_price(exchange_id, symbol)
                tasks.append(task)

        price_data = {}

        # 동시 실행 및 결과 수집
        if tasks:
            completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)

            for i, result in enumerate(completed_tasks):
                exchange_id = exchanges[i]

                if isinstance(result, Exception):
                    logger.warning(f"Failed to fetch price from {exchange_id}: {result}")
                    self._update_failure_stats(exchange_id)
                elif result and result.close > 0:
                    price_data[exchange_id] = result.close

        return price_data

    async def _fetch_single_price(self, exchange_id: str, symbol: str) -> Optional[TickerData]:
        """단일 거래소에서 가격 수집"""
        try:
            return await self.ccxt_manager.fetch_ticker(exchange_id, symbol)
        except Exception as e:
            logger.debug(f"Price fetch failed {exchange_id}:{symbol}: {e}")
            return None

    async def _fetch_ohlcv_from_exchanges(self, symbol: str, timeframe: str,
                                        exchanges: List[str], since: Optional[datetime],
                                        limit: int) -> Dict[str, List[OHLCVData]]:
        """다중 거래소에서 OHLCV 데이터 수집"""
        tasks = []

        for exchange_id in exchanges:
            if exchange_id in self.ccxt_manager.exchanges:
                task = self._fetch_single_ohlcv(exchange_id, symbol, timeframe, since, limit)
                tasks.append((exchange_id, task))

        ohlcv_data = {}

        # 결과 수집
        for exchange_id, task in tasks:
            try:
                result = await task
                if result:
                    ohlcv_data[exchange_id] = result
            except Exception as e:
                logger.warning(f"OHLCV fetch failed {exchange_id}:{symbol}: {e}")
                self._update_failure_stats(exchange_id)

        return ohlcv_data

    async def _fetch_single_ohlcv(self, exchange_id: str, symbol: str, timeframe: str,
                                since: Optional[datetime], limit: int) -> Optional[List[OHLCVData]]:
        """단일 거래소에서 OHLCV 수집"""
        try:
            return await self.ccxt_manager.fetch_ohlcv(exchange_id, symbol, timeframe, since, limit)
        except Exception as e:
            logger.debug(f"OHLCV fetch failed {exchange_id}:{symbol}: {e}")
            return None

    async def _unify_ohlcv_data(self, ohlcv_data: Dict[str, List[OHLCVData]],
                              request: DataRequest) -> UnifiedMarketData:
        """OHLCV 데이터 통합"""
        if not ohlcv_data:
            return UnifiedMarketData(
                symbol=request.symbol,
                timeframe=request.timeframe,
                data=pd.DataFrame(),
                sources=[],
                metadata={'error': 'No data available'}
            )

        # 가장 많은 데이터를 가진 소스를 기준으로 사용
        primary_source = max(ohlcv_data.keys(), key=lambda k: len(ohlcv_data[k]))
        primary_data = ohlcv_data[primary_source]

        # DataFrame 생성
        df_data = []
        for candle in primary_data:
            df_data.append({
                'timestamp': candle.timestamp,
                'open': candle.open,
                'high': candle.high,
                'low': candle.low,
                'close': candle.close,
                'volume': candle.volume
            })

        df = pd.DataFrame(df_data)

        if not df.empty:
            df.set_index('timestamp', inplace=True)
            df.sort_index(inplace=True)

        # 검증 결과 (종가 기준)
        validation_result = None
        if request.require_validation and len(ohlcv_data) >= 2:
            # 최신 종가들로 검증
            latest_closes = {}
            for source, data in ohlcv_data.items():
                if data:
                    latest_closes[source] = data[-1].close

            if len(latest_closes) >= 2:
                data_points = [
                    DataPoint(value=price, timestamp=datetime.now(), source=source)
                    for source, price in latest_closes.items()
                ]
                validation_result = await self.price_validator.validator.validate_price_data(
                    request.symbol, data_points
                )

        return UnifiedMarketData(
            symbol=request.symbol,
            timeframe=request.timeframe,
            data=df,
            sources=list(ohlcv_data.keys()),
            validation_result=validation_result,
            metadata={
                'primary_source': primary_source,
                'total_candles': len(df),
                'source_count': len(ohlcv_data)
            }
        )

    def _update_failure_stats(self, exchange_id: str):
        """실패 통계 업데이트"""
        if exchange_id not in self.fetch_stats['source_failures']:
            self.fetch_stats['source_failures'][exchange_id] = 0
        self.fetch_stats['source_failures'][exchange_id] += 1

    def get_fetch_statistics(self) -> Dict[str, Any]:
        """수집 통계 반환"""
        total_requests = self.fetch_stats['total_requests']
        cache_hits = self.fetch_stats['cache_hits']

        stats = {
            'total_requests': total_requests,
            'cache_hits': cache_hits,
            'cache_hit_rate': (cache_hits / total_requests * 100) if total_requests > 0 else 0,
            'validation_failures': self.fetch_stats['validation_failures'],
            'source_failures': self.fetch_stats['source_failures'],
            'cache_size': len(self.data_cache)
        }

        return stats

    async def clear_cache(self):
        """캐시 초기화"""
        self.data_cache.clear()
        logger.info("Data cache cleared")

    async def get_best_exchanges_for_symbol(self, symbol: str) -> List[str]:
        """심볼에 최적화된 거래소 목록 반환"""
        # 실제 구현에서는 거래량, 스프레드, 안정성 등을 고려
        all_exchanges = self.ccxt_manager.get_active_exchanges()

        # 임시로 에러율이 낮은 순으로 정렬
        exchange_scores = []
        for exchange_id in all_exchanges:
            error_count = self.fetch_stats['source_failures'].get(exchange_id, 0)
            score = 1.0 / (1.0 + error_count)  # 에러가 적을수록 높은 점수
            exchange_scores.append((exchange_id, score))

        # 점수 순으로 정렬
        exchange_scores.sort(key=lambda x: x[1], reverse=True)

        return [ex[0] for ex in exchange_scores[:5]]  # 상위 5개만 반환


class RealTimeDataStreamer:
    """실시간 데이터 스트리밍 (WebSocket 기반)"""

    def __init__(self, unified_fetcher: UnifiedDataFetcher):
        self.unified_fetcher = unified_fetcher
        self.active_streams: Dict[str, bool] = {}
        self.stream_data: Dict[str, Dict] = {}

    async def start_price_stream(self, symbols: List[str],
                               callback: callable, update_interval: int = 5):
        """가격 스트림 시작"""
        stream_id = f"price_stream_{len(self.active_streams)}"
        self.active_streams[stream_id] = True

        try:
            while self.active_streams.get(stream_id, False):
                # 현재 가격 수집
                price_data = await self.unified_fetcher.fetch_current_prices(symbols)

                # 콜백 호출
                await callback(price_data)

                # 다음 업데이트까지 대기
                await asyncio.sleep(update_interval)

        except Exception as e:
            logger.error(f"Price stream error: {e}")
        finally:
            self.active_streams[stream_id] = False

    def stop_stream(self, stream_id: str):
        """스트림 중지"""
        if stream_id in self.active_streams:
            self.active_streams[stream_id] = False

    def stop_all_streams(self):
        """모든 스트림 중지"""
        for stream_id in list(self.active_streams.keys()):
            self.active_streams[stream_id] = False