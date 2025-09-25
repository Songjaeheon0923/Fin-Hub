"""
Portfolio Spoke Service Configuration
"""

from pydantic import Field
from pydantic_settings import BaseSettings


class PortfolioSpokeConfig(BaseSettings):
    """Portfolio Spoke Service configuration"""

    # Service identification
    service_name: str = "pfolio-spoke"
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
    max_assets: int = Field(default=20, alias="MAX_ASSETS")
    risk_free_rate: float = Field(default=0.02, alias="RISK_FREE_RATE")  # 2%
    max_weight: float = Field(default=0.4, alias="MAX_WEIGHT")  # 40%
    min_weight: float = Field(default=0.01, alias="MIN_WEIGHT")  # 1%

    # Rebalancing settings
    rebalance_threshold: float = Field(default=0.05, alias="REBALANCE_THRESHOLD")  # 5%
    rebalance_frequency: str = Field(default="quarterly", alias="REBALANCE_FREQUENCY")

    class Config:
        env_file = ".env"
        case_sensitive = False