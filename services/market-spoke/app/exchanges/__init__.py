"""
CCXT 다중 거래소 통합 시스템
Freqtrade 방식 100+ 거래소 표준화 API
"""

from .ccxt_manager import CCXTManager, ExchangeConfig
from .exchange_registry import ExchangeRegistry
from .rate_limiter import RateLimiter
from .data_fetcher import UnifiedDataFetcher

__version__ = "1.0.0"

# 지원되는 거래소 목록 (주요 거래소)
SUPPORTED_EXCHANGES = [
    'binance', 'coinbase', 'kraken', 'bitfinex', 'huobi',
    'kucoin', 'gate', 'okex', 'bybit', 'ftx', 'gemini',
    'bitstamp', 'bittrex', 'poloniex', 'bithumb'
]

# 거래소별 기본 설정
DEFAULT_EXCHANGE_CONFIGS = {
    'binance': {
        'name': 'Binance',
        'countries': ['JP', 'MT'],
        'rateLimit': 1200,
        'has': {
            'fetchTicker': True,
            'fetchOHLCV': True,
            'fetchOrderBook': True,
            'fetchTrades': True
        }
    },
    'coinbase': {
        'name': 'Coinbase Pro',
        'countries': ['US'],
        'rateLimit': 10000,
        'has': {
            'fetchTicker': True,
            'fetchOHLCV': True,
            'fetchOrderBook': True,
            'fetchTrades': True
        }
    },
    'kraken': {
        'name': 'Kraken',
        'countries': ['US'],
        'rateLimit': 3000,
        'has': {
            'fetchTicker': True,
            'fetchOHLCV': True,
            'fetchOrderBook': True,
            'fetchTrades': True
        }
    }
}