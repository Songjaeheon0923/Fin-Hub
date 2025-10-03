"""
Portfolio Spoke Service Configuration
"""

from pydantic import Field
from pydantic_settings import BaseSettings


class PortfolioSpokeConfig(BaseSettings):
    """Portfolio Spoke Service configuration"""

    # Service identification
    service_name: str = "portfolio-spoke"
    version: str = "1.0.0"

    # Service network settings
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8003, alias="PORT")

    # Hub server connection
    hub_host: str = Field(default="hub-server", alias="HUB_HOST")
    hub_port: int = Field(default=8000, alias="HUB_PORT")

    # Consul settings
    consul_host: str = Field(default="consul", alias="CONSUL_HOST")
    consul_port: int = Field(default=8500, alias="CONSUL_PORT")

    # Portfolio optimization settings
    min_weight: float = Field(default=0.0, alias="MIN_WEIGHT")
    max_weight: float = Field(default=1.0, alias="MAX_WEIGHT")
    risk_free_rate: float = Field(default=0.02, alias="RISK_FREE_RATE")  # 2% annual

    # Rebalancing settings
    rebalance_threshold: float = Field(default=0.05, alias="REBALANCE_THRESHOLD")  # 5%
    min_trade_size: float = Field(default=100, alias="MIN_TRADE_SIZE")  # $100

    # Tax optimization settings
    tax_loss_harvest_threshold: float = Field(default=0.03, alias="TLH_THRESHOLD")  # 3%
    wash_sale_days: int = Field(default=30, alias="WASH_SALE_DAYS")

    class Config:
        env_file = ".env"
        case_sensitive = False
