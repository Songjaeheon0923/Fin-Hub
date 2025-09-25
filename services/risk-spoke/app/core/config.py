"""
Risk Spoke Service Configuration
"""

from pydantic import Field
from pydantic_settings import BaseSettings


class RiskSpokeConfig(BaseSettings):
    """Risk Spoke Service configuration"""

    # Service identification
    service_name: str = "risk-spoke"
    version: str = "1.0.0"

    # Service network settings
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8002, alias="PORT")

    # Hub server connection
    hub_host: str = Field(default="hub-server", alias="HUB_HOST")
    hub_port: int = Field(default=8000, alias="HUB_PORT")

    # Consul settings
    consul_host: str = Field(default="consul", alias="CONSUL_HOST")
    consul_port: int = Field(default=8500, alias="CONSUL_PORT")

    # Risk analysis settings
    anomaly_threshold: float = Field(default=0.95, alias="ANOMALY_THRESHOLD")  # 95th percentile
    risk_lookback_days: int = Field(default=30, alias="RISK_LOOKBACK_DAYS")
    max_transaction_amount: float = Field(default=1000000, alias="MAX_TRANSACTION_AMOUNT")

    # Compliance settings
    compliance_rules_enabled: bool = Field(default=True, alias="COMPLIANCE_ENABLED")
    kyc_required_threshold: float = Field(default=10000, alias="KYC_THRESHOLD")

    class Config:
        env_file = ".env"
        case_sensitive = False