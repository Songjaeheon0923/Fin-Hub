"""
Market Analysis Tools
Enhanced with Phase 1 API integrations and Unified API Manager
"""

# Import only existing modules
try:
    from .price_analyzer import PriceAnalyzer
    from .volatility_predictor import VolatilityPredictor
    from .sentiment_analyzer import SentimentAnalyzer
except ImportError:
    pass

# Import unified API tools
try:
    from .unified_market_data import (
        UnifiedMarketDataTool,
        StockQuoteTool,
        CryptoPriceTool,
        FinancialNewsTool,
        EconomicIndicatorTool,
        MarketOverviewTool,
        APIStatusTool
    )
except ImportError:
    pass

__all__ = [
    'PriceAnalyzer',
    'VolatilityPredictor',
    'SentimentAnalyzer',
    'UnifiedMarketDataTool',
    'StockQuoteTool',
    'CryptoPriceTool',
    'FinancialNewsTool',
    'EconomicIndicatorTool',
    'MarketOverviewTool',
    'APIStatusTool'
]