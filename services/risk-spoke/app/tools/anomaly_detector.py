"""
Anomaly Detector Tool - Detect unusual transaction patterns
"""
import random
import math
from datetime import datetime, timedelta
from typing import Dict, Any, List

from .base_tool import BaseTool


class AnomalyDetector(BaseTool):
    """Tool for detecting anomalous transactions"""

    def __init__(self):
        super().__init__(
            tool_id="risk.detect_anomaly",
            name="Detect Anomaly",
            description="이상거래를 탐지합니다"
        )

    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute anomaly detection"""
        try:
            # Validate required arguments
            self.validate_arguments(arguments, ["transaction_data"])

            transaction_data = arguments["transaction_data"]
            threshold = arguments.get("threshold", 0.95)
            analysis_type = arguments.get("analysis_type", "statistical")

            print(f"Analyzing transaction for anomalies, threshold: {threshold}")

            # Mock anomaly detection (in real implementation, use ML models)
            anomaly_result = await self._detect_mock_anomaly(
                transaction_data, threshold, analysis_type
            )

            return self.create_success_response(
                data=anomaly_result,
                metadata={
                    "threshold": threshold,
                    "analysis_type": analysis_type,
                    "model_version": "mock_v1.0",
                    "timestamp": datetime.now().isoformat()
                }
            )

        except Exception as e:
            return await self.handle_error(e, "anomaly_detection")

    async def get_tool_info(self) -> Dict[str, Any]:
        """Get tool information for MCP schema"""
        return {
            "name": self.tool_id,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": {
                    "transaction_data": {
                        "type": "object",
                        "description": "Transaction data to analyze",
                        "properties": {
                            "amount": {"type": "number", "minimum": 0},
                            "from_account": {"type": "string"},
                            "to_account": {"type": "string"},
                            "transaction_type": {"type": "string"},
                            "timestamp": {"type": "string"},
                            "location": {"type": "string"},
                            "device_id": {"type": "string"},
                            "user_id": {"type": "string"}
                        },
                        "required": ["amount", "from_account", "to_account", "transaction_type"]
                    },
                    "threshold": {
                        "type": "number",
                        "description": "Anomaly detection threshold (0.9 = 90th percentile)",
                        "minimum": 0.5,
                        "maximum": 0.99,
                        "default": 0.95
                    },
                    "analysis_type": {
                        "type": "string",
                        "enum": ["statistical", "ml_model", "rule_based", "hybrid"],
                        "description": "Type of anomaly detection analysis",
                        "default": "statistical"
                    }
                },
                "required": ["transaction_data"]
            }
        }

    async def _detect_mock_anomaly(self, transaction: Dict[str, Any], threshold: float,
                                  analysis_type: str) -> Dict[str, Any]:
        """Mock anomaly detection implementation"""

        amount = transaction.get("amount", 0)
        transaction_type = transaction.get("transaction_type", "transfer")
        user_id = transaction.get("user_id", "unknown")
        timestamp = transaction.get("timestamp", datetime.now().isoformat())
        location = transaction.get("location", "unknown")
        device_id = transaction.get("device_id", "unknown")

        # Calculate mock anomaly scores
        anomaly_scores = {}
        overall_risk_factors = []

        # Amount-based anomaly
        amount_score = await self._analyze_amount_anomaly(amount)
        anomaly_scores["amount"] = amount_score
        if amount_score > threshold:
            overall_risk_factors.append("unusual_amount")

        # Time-based anomaly
        time_score = await self._analyze_time_anomaly(timestamp)
        anomaly_scores["timing"] = time_score
        if time_score > threshold:
            overall_risk_factors.append("unusual_timing")

        # Location-based anomaly
        location_score = await self._analyze_location_anomaly(location, user_id)
        anomaly_scores["location"] = location_score
        if location_score > threshold:
            overall_risk_factors.append("unusual_location")

        # Device-based anomaly
        device_score = await self._analyze_device_anomaly(device_id, user_id)
        anomaly_scores["device"] = device_score
        if device_score > threshold:
            overall_risk_factors.append("unusual_device")

        # Pattern-based anomaly
        pattern_score = await self._analyze_pattern_anomaly(transaction)
        anomaly_scores["pattern"] = pattern_score
        if pattern_score > threshold:
            overall_risk_factors.append("unusual_pattern")

        # Calculate overall anomaly score
        overall_score = max(anomaly_scores.values())
        is_anomaly = overall_score > threshold

        # Generate detailed analysis
        risk_level = await self._calculate_risk_level(overall_score)
        recommendations = await self._generate_anomaly_recommendations(
            is_anomaly, overall_risk_factors, overall_score
        )

        # Generate similar transactions for context
        similar_transactions = await self._find_similar_transactions(transaction)

        return {
            "transaction_id": transaction.get("transaction_id", f"tx_{random.randint(100000, 999999)}"),
            "anomaly_detected": is_anomaly,
            "overall_anomaly_score": round(overall_score, 4),
            "risk_level": risk_level,
            "confidence": round(random.uniform(0.7, 0.95), 3),
            "anomaly_breakdown": {
                "amount_anomaly": {
                    "score": round(amount_score, 4),
                    "is_anomaly": amount_score > threshold,
                    "description": await self._get_amount_description(amount_score, amount)
                },
                "timing_anomaly": {
                    "score": round(time_score, 4),
                    "is_anomaly": time_score > threshold,
                    "description": await self._get_timing_description(time_score, timestamp)
                },
                "location_anomaly": {
                    "score": round(location_score, 4),
                    "is_anomaly": location_score > threshold,
                    "description": await self._get_location_description(location_score, location)
                },
                "device_anomaly": {
                    "score": round(device_score, 4),
                    "is_anomaly": device_score > threshold,
                    "description": await self._get_device_description(device_score, device_id)
                },
                "pattern_anomaly": {
                    "score": round(pattern_score, 4),
                    "is_anomaly": pattern_score > threshold,
                    "description": await self._get_pattern_description(pattern_score, transaction_type)
                }
            },
            "risk_factors": overall_risk_factors,
            "recommendations": recommendations,
            "similar_transactions": similar_transactions,
            "model_details": {
                "analysis_type": analysis_type,
                "threshold": threshold,
                "features_analyzed": list(anomaly_scores.keys()),
                "model_accuracy": random.uniform(0.85, 0.95)
            },
            "timestamp": datetime.now().isoformat()
        }

    async def _analyze_amount_anomaly(self, amount: float) -> float:
        """Analyze if transaction amount is anomalous"""
        # Mock logic: higher amounts are more anomalous
        if amount > 100000:
            return random.uniform(0.85, 0.98)
        elif amount > 50000:
            return random.uniform(0.70, 0.90)
        elif amount > 10000:
            return random.uniform(0.40, 0.75)
        else:
            return random.uniform(0.10, 0.50)

    async def _analyze_time_anomaly(self, timestamp_str: str) -> float:
        """Analyze if transaction timing is anomalous"""
        try:
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            hour = dt.hour

            # Business hours (9-17) are normal, night hours are more anomalous
            if 9 <= hour <= 17:
                return random.uniform(0.10, 0.30)
            elif 18 <= hour <= 22 or 6 <= hour <= 8:
                return random.uniform(0.30, 0.60)
            else:  # Late night/early morning
                return random.uniform(0.70, 0.95)
        except:
            return random.uniform(0.40, 0.70)

    async def _analyze_location_anomaly(self, location: str, user_id: str) -> float:
        """Analyze if transaction location is anomalous"""
        # Mock logic based on location patterns
        if location == "unknown":
            return random.uniform(0.60, 0.80)
        elif "foreign" in location.lower():
            return random.uniform(0.75, 0.95)
        else:
            return random.uniform(0.10, 0.50)

    async def _analyze_device_anomaly(self, device_id: str, user_id: str) -> float:
        """Analyze if device is anomalous for user"""
        # Mock logic: unknown devices are more risky
        if device_id == "unknown":
            return random.uniform(0.70, 0.90)
        else:
            return random.uniform(0.15, 0.45)

    async def _analyze_pattern_anomaly(self, transaction: Dict[str, Any]) -> float:
        """Analyze if transaction pattern is anomalous"""
        # Mock pattern analysis
        transaction_type = transaction.get("transaction_type", "")

        if transaction_type in ["wire_transfer", "crypto"]:
            return random.uniform(0.60, 0.85)
        elif transaction_type in ["cash_withdrawal", "international"]:
            return random.uniform(0.45, 0.75)
        else:
            return random.uniform(0.10, 0.40)

    async def _calculate_risk_level(self, score: float) -> str:
        """Calculate risk level based on anomaly score"""
        if score >= 0.9:
            return "critical"
        elif score >= 0.8:
            return "high"
        elif score >= 0.6:
            return "medium"
        elif score >= 0.4:
            return "low"
        else:
            return "minimal"

    async def _generate_anomaly_recommendations(self, is_anomaly: bool,
                                              risk_factors: List[str],
                                              score: float) -> List[str]:
        """Generate recommendations based on anomaly analysis"""
        recommendations = []

        if not is_anomaly:
            recommendations.append("Transaction appears normal - no action required")
            return recommendations

        if score >= 0.9:
            recommendations.append("URGENT: Block transaction immediately and investigate")
            recommendations.append("Contact customer to verify transaction legitimacy")

        if "unusual_amount" in risk_factors:
            recommendations.append("Verify large amount transaction with additional authentication")

        if "unusual_location" in risk_factors:
            recommendations.append("Check if customer is traveling or has moved")

        if "unusual_timing" in risk_factors:
            recommendations.append("Verify off-hours transaction with customer")

        if "unusual_device" in risk_factors:
            recommendations.append("Implement additional device verification")

        if "unusual_pattern" in risk_factors:
            recommendations.append("Review recent transaction history for patterns")

        # General recommendations
        recommendations.append("Document investigation findings")
        recommendations.append("Consider adjusting customer risk profile")

        return recommendations[:6]

    async def _find_similar_transactions(self, transaction: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find similar transactions for context (mock data)"""
        similar = []
        base_amount = transaction.get("amount", 1000)

        for i in range(3):
            similar_amount = base_amount * random.uniform(0.8, 1.2)
            days_ago = random.randint(1, 30)
            date = datetime.now() - timedelta(days=days_ago)

            similar.append({
                "transaction_id": f"similar_tx_{random.randint(10000, 99999)}",
                "amount": round(similar_amount, 2),
                "date": date.strftime("%Y-%m-%d"),
                "anomaly_score": round(random.uniform(0.1, 0.7), 3),
                "status": random.choice(["completed", "flagged", "investigated"])
            })

        return similar

    async def _get_amount_description(self, score: float, amount: float) -> str:
        """Get description for amount anomaly"""
        if score > 0.8:
            return f"Amount ${amount:,.2f} is significantly higher than typical transactions"
        elif score > 0.6:
            return f"Amount ${amount:,.2f} is moderately higher than usual"
        else:
            return f"Amount ${amount:,.2f} is within normal range"

    async def _get_timing_description(self, score: float, timestamp: str) -> str:
        """Get description for timing anomaly"""
        if score > 0.8:
            return f"Transaction time is highly unusual for this customer"
        elif score > 0.6:
            return f"Transaction occurred outside normal business hours"
        else:
            return f"Transaction timing appears normal"

    async def _get_location_description(self, score: float, location: str) -> str:
        """Get description for location anomaly"""
        if score > 0.8:
            return f"Location '{location}' is highly unusual for this customer"
        elif score > 0.6:
            return f"Location '{location}' is different from typical patterns"
        else:
            return f"Location '{location}' matches customer's typical patterns"

    async def _get_device_description(self, score: float, device_id: str) -> str:
        """Get description for device anomaly"""
        if score > 0.8:
            return f"Device '{device_id}' has never been used by this customer"
        elif score > 0.6:
            return f"Device '{device_id}' is rarely used by this customer"
        else:
            return f"Device '{device_id}' is recognized for this customer"

    async def _get_pattern_description(self, score: float, transaction_type: str) -> str:
        """Get description for pattern anomaly"""
        if score > 0.8:
            return f"Transaction type '{transaction_type}' is highly unusual for this customer"
        elif score > 0.6:
            return f"Transaction type '{transaction_type}' is uncommon for this customer"
        else:
            return f"Transaction type '{transaction_type}' is normal for this customer"