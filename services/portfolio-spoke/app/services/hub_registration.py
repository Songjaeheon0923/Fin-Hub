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
            "type": "portfolio-spoke",
            "host": self.config.host,
            "port": self.config.port,
            "health_check": f"http://{self.config.host}:{self.config.port}/health",
            "mcp_endpoint": f"http://{self.config.host}:{self.config.port}/mcp",
            "capabilities": ["portfolio_optimization", "rebalancing", "performance_analysis", "tax_optimization"],
            "tools": [
                {
                    "id": "portfolio.optimize",
                    "name": "Portfolio Optimizer",
                    "description": "포트폴리오 최적화를 수행합니다",
                    "category": "optimization"
                },
                {
                    "id": "portfolio.rebalance",
                    "name": "Portfolio Rebalancer",
                    "description": "포트폴리오 리밸런싱을 수행합니다",
                    "category": "rebalancing"
                },
                {
                    "id": "portfolio.analyze_performance",
                    "name": "Performance Analyzer",
                    "description": "포트폴리오 성과를 분석합니다",
                    "category": "analysis"
                },
                {
                    "id": "portfolio.backtest",
                    "name": "Backtester",
                    "description": "전략 백테스팅을 수행합니다",
                    "category": "testing"
                },
                {
                    "id": "portfolio.analyze_factors",
                    "name": "Factor Analyzer",
                    "description": "팩터 분석을 수행합니다",
                    "category": "analysis"
                },
                {
                    "id": "portfolio.allocate_assets",
                    "name": "Asset Allocator",
                    "description": "자산 배분을 수행합니다",
                    "category": "allocation"
                },
                {
                    "id": "portfolio.optimize_tax",
                    "name": "Tax Optimizer",
                    "description": "세금 최적화를 수행합니다",
                    "category": "optimization"
                },
                {
                    "id": "portfolio.dashboard",
                    "name": "Portfolio Dashboard",
                    "description": "포트폴리오 대시보드를 생성합니다",
                    "category": "dashboard"
                }
            ],
            "tags": ["portfolio", "optimization", "rebalancing", "analysis", "tax"],
            "metadata": {
                "author": "Fin-Hub Team",
                "documentation": f"http://{self.config.host}:{self.config.port}/docs"
            }
        }
