"""
Market Spoke Service Configuration
"""

import os
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from shared.config.base import BaseServiceConfig


class MarketSpokeConfig(BaseServiceConfig):
    """Market Spoke Service configuration"""

    # Service identification
    service_name: str = "market-spoke"
    service_id: str = Field(default_factory=lambda: f"market-spoke-{os.getenv('HOSTNAME', 'local')}")
    version: str = "1.0.0"

    # Market data providers
    alpha_vantage_api_key: Optional[str] = Field(default=None, alias="ALPHA_VANTAGE_API_KEY")
    fred_api_key: Optional[str] = Field(default=None, alias="FRED_API_KEY")

    # Yahoo Finance settings
    yfinance_timeout: int = Field(default=10, alias="YFINANCE_TIMEOUT")

    # News settings
    news_sources: List[str] = Field(
        default=[
            "https://feeds.finance.yahoo.com/rss/2.0/headline",
            "https://www.marketwatch.com/rss/topstories",
            "https://www.cnbc.com/id/100003114/device/rss/rss.html"
        ],
        alias="NEWS_SOURCES"
    )

    # Cache settings
    cache_ttl_seconds: int = Field(default=300, alias="CACHE_TTL_SECONDS")  # 5 minutes

    # Rate limiting
    rate_limit_per_minute: int = Field(default=100, alias="RATE_LIMIT_PER_MINUTE")

    # Technical analysis settings
    default_period: int = Field(default=20, alias="DEFAULT_TA_PERIOD")
    max_historical_days: int = Field(default=365, alias="MAX_HISTORICAL_DAYS")

    # Hub server connection
    hub_server_url: str = Field(default="http://hub-server:8000", alias="HUB_SERVER_URL")

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global config instance
_config = None


def get_config() -> MarketSpokeConfig:
    """Get configuration instance"""
    global _config
    if _config is None:
        _config = MarketSpokeConfig()
    return _config