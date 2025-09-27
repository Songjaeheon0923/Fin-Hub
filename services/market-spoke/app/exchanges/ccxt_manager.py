"""
CCXT 거래소 관리자
Freqtrade 스타일 통합 거래소 API
"""

import ccxt
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import logging
from contextlib import asynccontextmanager
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


logger = logging.getLogger(__name__)


@dataclass
class ExchangeConfig:
    """거래소 설정"""
    exchange_id: str
    name: str
    api_key: Optional[str] = None
    secret: Optional[str] = None
    password: Optional[str] = None
    sandbox: bool = True
    rate_limit: int = 1000  # ms
    timeout: int = 30000  # ms
    enabled: bool = True
    supported_timeframes: List[str] = field(default_factory=lambda: ['1m', '5m', '15m', '1h', '4h', '1d'])
    fees: Dict[str, float] = field(default_factory=dict)
    min_trade_amount: Dict[str, float] = field(default_factory=dict)


@dataclass
class MarketInfo:
    """시장 정보"""
    symbol: str
    base: str
    quote: str
    active: bool
    min_amount: float
    max_amount: float
    min_cost: float
    precision: Dict[str, int]
    fees: Dict[str, float]


@dataclass
class TickerData:
    """티커 데이터"""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    bid: Optional[float] = None
    ask: Optional[float] = None
    bid_volume: Optional[float] = None
    ask_volume: Optional[float] = None
    change: Optional[float] = None
    percentage: Optional[float] = None


@dataclass
class OHLCVData:
    """OHLCV 캔들 데이터"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class CCXTManager:
    """CCXT 거래소 통합 관리자"""

    def __init__(self):
        self.exchanges: Dict[str, ccxt.Exchange] = {}
        self.configs: Dict[str, ExchangeConfig] = {}
        self.markets_cache: Dict[str, Dict[str, MarketInfo]] = {}
        self.rate_limiters: Dict[str, Any] = {}
        self.last_requests: Dict[str, float] = {}

        # 비동기 실행을 위한 스레드 풀
        self.executor = ThreadPoolExecutor(max_workers=10)

        # 거래소별 상태 추적
        self.exchange_status: Dict[str, bool] = {}
        self.error_counts: Dict[str, int] = {}

    async def initialize_exchange(self, config: ExchangeConfig) -> bool:
        """거래소 초기화"""
        try:
            # CCXT 거래소 클래스 가져오기
            exchange_class = getattr(ccxt, config.exchange_id)

            # 거래소 인스턴스 생성
            exchange_config = {
                'apiKey': config.api_key,
                'secret': config.secret,
                'password': config.password,
                'sandbox': config.sandbox,
                'rateLimit': config.rate_limit,
                'timeout': config.timeout,
                'enableRateLimit': True,
                'options': {
                    'adjustForTimeDifference': True,
                    'recvWindow': 60000,
                }
            }

            # None 값 제거
            exchange_config = {k: v for k, v in exchange_config.items() if v is not None}

            exchange = exchange_class(exchange_config)

            # 비동기 지원 확인
            if hasattr(exchange, 'load_markets'):
                await self._run_in_executor(exchange.load_markets)

            self.exchanges[config.exchange_id] = exchange
            self.configs[config.exchange_id] = config
            self.exchange_status[config.exchange_id] = True
            self.error_counts[config.exchange_id] = 0

            logger.info(f"Initialized exchange: {config.exchange_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize {config.exchange_id}: {e}")
            self.exchange_status[config.exchange_id] = False
            return False

    async def get_markets(self, exchange_id: str, force_reload: bool = False) -> Dict[str, MarketInfo]:
        """시장 정보 조회"""
        if not force_reload and exchange_id in self.markets_cache:
            return self.markets_cache[exchange_id]

        try:
            exchange = self.exchanges.get(exchange_id)
            if not exchange:
                raise ValueError(f"Exchange {exchange_id} not initialized")

            # 마켓 데이터 로드
            markets = await self._run_in_executor(exchange.load_markets)

            # MarketInfo 객체로 변환
            market_info = {}
            for symbol, market in markets.items():
                info = MarketInfo(
                    symbol=symbol,
                    base=market['base'],
                    quote=market['quote'],
                    active=market.get('active', True),
                    min_amount=market['limits']['amount']['min'] or 0.0,
                    max_amount=market['limits']['amount']['max'] or float('inf'),
                    min_cost=market['limits']['cost']['min'] or 0.0,
                    precision=market['precision'],
                    fees=market.get('fees', {})
                )
                market_info[symbol] = info

            self.markets_cache[exchange_id] = market_info
            return market_info

        except Exception as e:
            logger.error(f"Error getting markets for {exchange_id}: {e}")
            return {}

    async def fetch_ticker(self, exchange_id: str, symbol: str) -> Optional[TickerData]:
        """티커 데이터 조회"""
        try:
            exchange = self.exchanges.get(exchange_id)
            if not exchange:
                return None

            await self._respect_rate_limit(exchange_id)

            ticker = await self._run_in_executor(exchange.fetch_ticker, symbol)

            return TickerData(
                symbol=ticker['symbol'],
                timestamp=datetime.fromtimestamp(ticker['timestamp'] / 1000),
                open=ticker['open'] or 0.0,
                high=ticker['high'] or 0.0,
                low=ticker['low'] or 0.0,
                close=ticker['close'] or 0.0,
                volume=ticker['baseVolume'] or 0.0,
                bid=ticker['bid'],
                ask=ticker['ask'],
                bid_volume=ticker['bidVolume'],
                ask_volume=ticker['askVolume'],
                change=ticker['change'],
                percentage=ticker['percentage']
            )

        except Exception as e:
            await self._handle_exchange_error(exchange_id, e)
            return None

    async def fetch_ohlcv(self, exchange_id: str, symbol: str, timeframe: str = '1d',
                         since: Optional[datetime] = None, limit: int = 100) -> List[OHLCVData]:
        """OHLCV 데이터 조회"""
        try:
            exchange = self.exchanges.get(exchange_id)
            if not exchange:
                return []

            await self._respect_rate_limit(exchange_id)

            # 시간 파라미터 변환
            since_timestamp = None
            if since:
                since_timestamp = int(since.timestamp() * 1000)

            ohlcv = await self._run_in_executor(
                exchange.fetch_ohlcv, symbol, timeframe, since_timestamp, limit
            )

            result = []
            for candle in ohlcv:
                data = OHLCVData(
                    timestamp=datetime.fromtimestamp(candle[0] / 1000),
                    open=candle[1],
                    high=candle[2],
                    low=candle[3],
                    close=candle[4],
                    volume=candle[5]
                )
                result.append(data)

            return result

        except Exception as e:
            await self._handle_exchange_error(exchange_id, e)
            return []

    async def fetch_multiple_tickers(self, exchange_id: str, symbols: List[str]) -> Dict[str, TickerData]:
        """다중 티커 데이터 조회"""
        try:
            exchange = self.exchanges.get(exchange_id)
            if not exchange:
                return {}

            await self._respect_rate_limit(exchange_id)

            # 거래소가 다중 티커 조회를 지원하는지 확인
            if hasattr(exchange, 'fetch_tickers'):
                tickers = await self._run_in_executor(exchange.fetch_tickers, symbols)
                result = {}

                for symbol, ticker in tickers.items():
                    if symbol in symbols:
                        result[symbol] = TickerData(
                            symbol=ticker['symbol'],
                            timestamp=datetime.fromtimestamp(ticker['timestamp'] / 1000),
                            open=ticker['open'] or 0.0,
                            high=ticker['high'] or 0.0,
                            low=ticker['low'] or 0.0,
                            close=ticker['close'] or 0.0,
                            volume=ticker['baseVolume'] or 0.0,
                            bid=ticker['bid'],
                            ask=ticker['ask'],
                            change=ticker['change'],
                            percentage=ticker['percentage']
                        )

                return result
            else:
                # 개별 조회로 폴백
                result = {}
                for symbol in symbols:
                    ticker = await self.fetch_ticker(exchange_id, symbol)
                    if ticker:
                        result[symbol] = ticker

                return result

        except Exception as e:
            await self._handle_exchange_error(exchange_id, e)
            return {}

    async def get_exchange_status(self, exchange_id: str) -> Dict[str, Any]:
        """거래소 상태 조회"""
        try:
            exchange = self.exchanges.get(exchange_id)
            if not exchange:
                return {'status': 'not_initialized', 'error': 'Exchange not found'}

            # 상태 확인을 위한 간단한 API 호출
            await self._run_in_executor(exchange.fetch_status)

            return {
                'status': 'online',
                'last_check': datetime.now().isoformat(),
                'error_count': self.error_counts.get(exchange_id, 0),
                'rate_limit': self.configs[exchange_id].rate_limit
            }

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }

    async def get_supported_symbols(self, exchange_id: str, base_currency: str = None) -> List[str]:
        """지원되는 심볼 목록 조회"""
        try:
            markets = await self.get_markets(exchange_id)

            symbols = []
            for symbol, market in markets.items():
                if market.active:
                    if base_currency is None or market.base == base_currency:
                        symbols.append(symbol)

            return sorted(symbols)

        except Exception as e:
            logger.error(f"Error getting symbols for {exchange_id}: {e}")
            return []

    async def get_exchange_fees(self, exchange_id: str, symbol: str) -> Dict[str, float]:
        """거래소 수수료 정보 조회"""
        try:
            exchange = self.exchanges.get(exchange_id)
            if not exchange:
                return {}

            # 마켓에서 수수료 정보 가져오기
            markets = await self.get_markets(exchange_id)
            market = markets.get(symbol)

            if market and market.fees:
                return market.fees

            # 기본 수수료 정보
            if hasattr(exchange, 'fees'):
                return exchange.fees.get('trading', {})

            return {}

        except Exception as e:
            logger.error(f"Error getting fees for {exchange_id}: {e}")
            return {}

    async def _run_in_executor(self, func, *args):
        """스레드 풀에서 동기 함수 실행"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, func, *args)

    async def _respect_rate_limit(self, exchange_id: str):
        """레이트 리미트 준수"""
        config = self.configs.get(exchange_id)
        if not config:
            return

        last_request = self.last_requests.get(exchange_id, 0)
        min_interval = config.rate_limit / 1000.0  # ms to seconds

        elapsed = time.time() - last_request
        if elapsed < min_interval:
            sleep_time = min_interval - elapsed
            await asyncio.sleep(sleep_time)

        self.last_requests[exchange_id] = time.time()

    async def _handle_exchange_error(self, exchange_id: str, error: Exception):
        """거래소 에러 처리"""
        self.error_counts[exchange_id] = self.error_counts.get(exchange_id, 0) + 1

        # 에러 타입별 처리
        if isinstance(error, ccxt.NetworkError):
            logger.warning(f"Network error for {exchange_id}: {error}")
            # 잠시 대기 후 재시도 가능
            await asyncio.sleep(1)
        elif isinstance(error, ccxt.ExchangeError):
            logger.error(f"Exchange error for {exchange_id}: {error}")
            # 거래소 문제 - 상태 업데이트
            self.exchange_status[exchange_id] = False
        elif isinstance(error, ccxt.RateLimitExceeded):
            logger.warning(f"Rate limit exceeded for {exchange_id}: {error}")
            # 더 긴 대기
            await asyncio.sleep(5)
        else:
            logger.error(f"Unknown error for {exchange_id}: {error}")

    def get_all_exchange_ids(self) -> List[str]:
        """모든 초기화된 거래소 ID 반환"""
        return list(self.exchanges.keys())

    def get_active_exchanges(self) -> List[str]:
        """활성화된 거래소 ID 반환"""
        return [eid for eid, status in self.exchange_status.items() if status]

    async def shutdown(self):
        """거래소 매니저 종료"""
        # 모든 거래소 연결 종료
        for exchange in self.exchanges.values():
            if hasattr(exchange, 'close'):
                try:
                    await self._run_in_executor(exchange.close)
                except Exception as e:
                    logger.error(f"Error closing exchange: {e}")

        # 스레드 풀 종료
        self.executor.shutdown(wait=True)

        logger.info("CCXT Manager shut down")


class ExchangeHealthMonitor:
    """거래소 상태 모니터링"""

    def __init__(self, ccxt_manager: CCXTManager):
        self.ccxt_manager = ccxt_manager
        self.health_history: Dict[str, List[Dict]] = {}
        self.monitoring_active = False

    async def start_monitoring(self, interval_seconds: int = 300):
        """모니터링 시작 (5분 간격)"""
        self.monitoring_active = True

        while self.monitoring_active:
            await self._check_all_exchanges()
            await asyncio.sleep(interval_seconds)

    async def stop_monitoring(self):
        """모니터링 중지"""
        self.monitoring_active = False

    async def _check_all_exchanges(self):
        """모든 거래소 상태 확인"""
        exchange_ids = self.ccxt_manager.get_all_exchange_ids()

        for exchange_id in exchange_ids:
            try:
                status = await self.ccxt_manager.get_exchange_status(exchange_id)

                # 히스토리에 기록
                if exchange_id not in self.health_history:
                    self.health_history[exchange_id] = []

                self.health_history[exchange_id].append({
                    'timestamp': datetime.now(),
                    'status': status['status'],
                    'response_time': 0  # 실제 구현시 응답 시간 측정
                })

                # 최근 24시간 데이터만 유지
                cutoff_time = datetime.now() - timedelta(hours=24)
                self.health_history[exchange_id] = [
                    h for h in self.health_history[exchange_id]
                    if h['timestamp'] > cutoff_time
                ]

            except Exception as e:
                logger.error(f"Error monitoring {exchange_id}: {e}")

    def get_health_report(self) -> Dict[str, Any]:
        """전체 상태 리포트 생성"""
        report = {}

        for exchange_id, history in self.health_history.items():
            if not history:
                continue

            total_checks = len(history)
            online_checks = sum(1 for h in history if h['status'] == 'online')
            uptime_percentage = (online_checks / total_checks) * 100

            report[exchange_id] = {
                'uptime_percentage': round(uptime_percentage, 2),
                'total_checks': total_checks,
                'last_status': history[-1]['status'] if history else 'unknown',
                'last_check': history[-1]['timestamp'].isoformat() if history else None
            }

        return report