"""
Market Analysis Tools
Enhanced with Phase 1 API integrations and Advanced Analysis Tools
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

# Import advanced analysis tools
try:
    from .technical_analysis import TechnicalAnalysisTool
    from .pattern_recognition import PatternRecognitionTool
    from .anomaly_detection import AnomalyDetectionTool
    from .stock_comparison import StockComparisonTool
    from .sentiment_analysis import SentimentAnalysisTool
    from .alert_system import AlertSystemTool
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
    'APIStatusTool',
    'TechnicalAnalysisTool',
    'PatternRecognitionTool',
    'AnomalyDetectionTool',
    'StockComparisonTool',
    'SentimentAnalysisTool',
    'AlertSystemTool'
]