"""
Hub Registration Service - Auto-register Portfolio Spoke with Hub
"""
import json
from typing import Dict, Any

import aiohttp
from app.core.config import PortfolioSpokeConfig


class HubRegistrationService:
    """Service to register Portfolio Spoke with the Hub"""

    def __init__(self):
        self.config = PortfolioSpokeConfig()
        self.hub_url = f"http://{self.config.hub_host}:{self.config.hub_port}"

    async def register(self) -> bool:
        """Register this Portfolio Spoke service with the Hub"""
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
                        print(f"Successfully registered with Hub: {result}")
                        return True
                    else:
                        error_text = await response.text()
                        print(f"Hub registration failed: {response.status} - {error_text}")
                        return False

        except Exception as e:
            print(f"Error during Hub registration: {e}")
            return False

    def _get_service_info(self) -> Dict[str, Any]:
        """Get service information for registration"""
        return {
            "name": self.config.service_name,
            "version": "1.0.0",
            "type": "pfolio-spoke",
            "host": self.config.host,
            "port": self.config.port,
            "health_check": f"http://{self.config.host}:{self.config.port}/health",
            "mcp_endpoint": f"http://{self.config.host}:{self.config.port}/mcp",
            "capabilities": ["portfolio_optimization", "rebalancing", "consumption_analysis"],
            "tools": [
                {
                    "id": "pfolio.generate_optimal",
                    "name": "Generate Optimal Portfolio",
                    "description": "최적 포트폴리오를 생성합니다",
                    "category": "optimization"
                },
                {
                    "id": "pfolio.rebalance_trigger",
                    "name": "Rebalancing Trigger",
                    "description": "리밸런싱 필요 여부를 확인합니다",
                    "category": "management"
                },
                {
                    "id": "pfolio.analyze_consumption",
                    "name": "Analyze Consumption",
                    "description": "소비 패턴을 분석합니다",
                    "category": "analysis"
                }
            ],
            "tags": ["portfolio", "optimization", "finance", "rebalancing"],
            "metadata": {
                "author": "Fin-Hub Team",
                "documentation": f"http://{self.config.host}:{self.config.port}/docs"
            }
        }