"""
Hub Registration Service - Auto-register Market Spoke with Hub
"""
import json
import os
import sys
from typing import Dict, Any

# Add shared directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

import aiohttp
from shared.utils.logging import setup_logging
from app.core.config import MarketSpokeConfig

logger = setup_logging("hub_registration")


class HubRegistrationService:
    """Service to register Market Spoke with the Hub"""

    def __init__(self):
        self.config = MarketSpokeConfig()
        self.hub_url = f"http://{self.config.hub_host}:{self.config.hub_port}"

    async def register(self) -> bool:
        """Register this Market Spoke service with the Hub"""
        try:
            service_info = self._get_service_info()

            async with aiohttp.ClientSession() as session:
                # Register service with Hub
                register_url = f"{self.hub_url}/api/v1/services/register"

                async with session.post(
                    register_url,
                    json=service_info,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Successfully registered with Hub: {result}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Hub registration failed: {response.status} - {error_text}")
                        return False

        except aiohttp.ClientError as e:
            logger.error(f"Network error during Hub registration: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during Hub registration: {e}")
            return False

    def _get_service_info(self) -> Dict[str, Any]:
        """Get service information for registration"""
        return {
            "name": self.config.service_name,
            "version": "1.0.0",
            "type": "market-spoke",
            "host": self.config.host,
            "port": self.config.port,
            "health_check": f"http://{self.config.host}:{self.config.port}/health",
            "mcp_endpoint": f"http://{self.config.host}:{self.config.port}/mcp",
            "capabilities": ["market_analysis", "price_data", "volatility_prediction", "sentiment_analysis"],
            "tools": [
                {
                    "id": "market.get_price",
                    "name": "Get Stock Price",
                    "description": "실시간 또는 과거 주가 데이터를 조회합니다",
                    "category": "market_data"
                },
                {
                    "id": "market.predict_volatility",
                    "name": "Predict Volatility",
                    "description": "주식의 변동성을 예측합니다",
                    "category": "analysis"
                },
                {
                    "id": "market.analyze_sentiment",
                    "name": "Analyze Market Sentiment",
                    "description": "시장 감성을 분석합니다",
                    "category": "analysis"
                }
            ],
            "tags": ["market", "analysis", "finance", "stocks"],
            "metadata": {
                "author": "Fin-Hub Team",
                "documentation": f"http://{self.config.host}:{self.config.port}/docs",
                "source_code": "https://github.com/fin-hub/market-spoke"
            }
        }

    async def deregister(self) -> bool:
        """Deregister this service from the Hub"""
        try:
            async with aiohttp.ClientSession() as session:
                deregister_url = f"{self.hub_url}/api/v1/services/{self.config.service_name}"

                async with session.delete(
                    deregister_url,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status in [200, 204, 404]:  # 404 is OK (already deregistered)
                        logger.info("Successfully deregistered from Hub")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Hub deregistration failed: {response.status} - {error_text}")
                        return False

        except aiohttp.ClientError as e:
            logger.error(f"Network error during Hub deregistration: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during Hub deregistration: {e}")
            return False

    async def update_health_status(self, status: str) -> bool:
        """Update health status with the Hub"""
        try:
            health_info = {
                "service_name": self.config.service_name,
                "status": status,
                "timestamp": None,  # Will be set by Hub
                "details": {
                    "host": self.config.host,
                    "port": self.config.port,
                    "version": "1.0.0"
                }
            }

            async with aiohttp.ClientSession() as session:
                health_url = f"{self.hub_url}/api/v1/services/{self.config.service_name}/health"

                async with session.put(
                    health_url,
                    json=health_info,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        return True
                    else:
                        logger.warning(f"Health status update failed: {response.status}")
                        return False

        except Exception as e:
            logger.warning(f"Failed to update health status: {e}")
            return False