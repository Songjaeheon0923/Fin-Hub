"""
Hub Registration Service - Auto-register Risk Spoke with Hub
"""
import json
from typing import Dict, Any

import aiohttp
from app.core.config import RiskSpokeConfig


class HubRegistrationService:
    """Service to register Risk Spoke with the Hub"""

    def __init__(self):
        self.config = RiskSpokeConfig()
        self.hub_url = f"http://{self.config.hub_host}:{self.config.hub_port}"

    async def register(self) -> bool:
        """Register this Risk Spoke service with the Hub"""
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
            "type": "risk-spoke",
            "host": self.config.host,
            "port": self.config.port,
            "health_check": f"http://{self.config.host}:{self.config.port}/health",
            "mcp_endpoint": f"http://{self.config.host}:{self.config.port}/mcp",
            "capabilities": ["anomaly_detection", "compliance_check", "risk_analysis"],
            "tools": [
                {
                    "id": "risk.detect_anomaly",
                    "name": "Detect Anomaly",
                    "description": "이상거래를 탐지합니다",
                    "category": "detection"
                },
                {
                    "id": "risk.check_compliance",
                    "name": "Check Compliance",
                    "description": "규제 준수 여부를 확인합니다",
                    "category": "compliance"
                }
            ],
            "tags": ["risk", "compliance", "anomaly", "detection"],
            "metadata": {
                "author": "Fin-Hub Team",
                "documentation": f"http://{self.config.host}:{self.config.port}/docs"
            }
        }