"""
Portfolio Optimizer Tool - Generate optimal portfolios
"""
import random
import math
from datetime import datetime
from typing import Dict, Any, List
import numpy as np
from scipy.optimize import minimize

from .base_tool import BaseTool


class PortfolioOptimizer(BaseTool):
    """Tool for optimizing portfolio allocation"""

    def __init__(self):
        super().__init__(
            tool_id="pfolio.generate_optimal",
            name="Generate Optimal Portfolio",
            description="최적 포트폴리오를 생성합니다"
        )

    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute portfolio optimization"""
        try:
            # Validate required arguments
            self.validate_arguments(arguments, ["assets"])

            assets = arguments["assets"]
            risk_tolerance = arguments.get("risk_tolerance", "moderate")
            investment_amount = arguments.get("investment_amount", 100000)
            objective = arguments.get("objective", "max_sharpe")

            print(f"Optimizing portfolio for {len(assets)} assets, risk: {risk_tolerance}")

            # Mock optimization (in real implementation, use Modern Portfolio Theory)
            portfolio_data = await self._optimize_mock_portfolio(
                assets, risk_tolerance, investment_amount, objective
            )

            return self.create_success_response(
                data=portfolio_data,
                metadata={
                    "assets_count": len(assets),
                    "risk_tolerance": risk_tolerance,
                    "objective": objective,
                    "optimization_method": "mock_mpt",
                    "timestamp": datetime.now().isoformat()
                }
            )

        except Exception as e:
            return await self.handle_error(e, "portfolio_optimization")

    async def get_tool_info(self) -> Dict[str, Any]:
        """Get tool information for MCP schema"""
        return {
            "name": self.tool_id,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": {
                    "assets": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of asset tickers (e.g., ['AAPL', 'GOOGL', 'MSFT'])"
                    },
                    "risk_tolerance": {
                        "type": "string",
                        "enum": ["conservative", "moderate", "aggressive"],
                        "description": "Risk tolerance level",
                        "default": "moderate"
                    },
                    "investment_amount": {
                        "type": "number",
                        "description": "Total investment amount in USD",
                        "minimum": 1000,
                        "default": 100000
                    },
                    "objective": {
                        "type": "string",
                        "enum": ["max_sharpe", "min_risk", "max_return"],
                        "description": "Optimization objective",
                        "default": "max_sharpe"
                    }
                },
                "required": ["assets"]
            }
        }

    async def _optimize_mock_portfolio(self, assets: List[str], risk_tolerance: str,
                                     investment_amount: float, objective: str) -> Dict[str, Any]:
        """Generate mock portfolio optimization"""

        # Risk tolerance parameters
        risk_params = {
            "conservative": {"target_return": 0.06, "max_volatility": 0.12, "diversification": 0.9},
            "moderate": {"target_return": 0.08, "max_volatility": 0.16, "diversification": 0.7},
            "aggressive": {"target_return": 0.12, "max_volatility": 0.25, "diversification": 0.5}
        }

        params = risk_params.get(risk_tolerance, risk_params["moderate"])

        # Generate mock expected returns and volatilities
        expected_returns = {}
        volatilities = {}

        for asset in assets:
            # Base returns on asset type (mock)
            base_return = params["target_return"]
            if "TECH" in asset or asset in ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA"]:
                base_return *= 1.2
            elif "BOND" in asset or asset in ["TLT", "AGG", "BND"]:
                base_return *= 0.6
            elif "REIT" in asset or asset in ["VNQ", "REIT"]:
                base_return *= 0.8

            expected_returns[asset] = base_return * (1 + random.uniform(-0.3, 0.3))
            volatilities[asset] = params["max_volatility"] * (1 + random.uniform(-0.4, 0.4))

        # Generate portfolio weights using mock optimization
        num_assets = len(assets)

        if objective == "min_risk":
            # Conservative allocation
            weights = self._generate_min_risk_weights(num_assets, params["diversification"])
        elif objective == "max_return":
            # Growth-focused allocation
            weights = self._generate_max_return_weights(assets, expected_returns)
        else:  # max_sharpe
            # Balanced allocation
            weights = self._generate_sharpe_weights(num_assets, params["diversification"])

        # Ensure weights sum to 1
        weights = np.array(weights)
        weights = weights / np.sum(weights)

        # Calculate portfolio metrics
        portfolio_return = sum(expected_returns[asset] * weight for asset, weight in zip(assets, weights))
        portfolio_volatility = self._calculate_portfolio_volatility(assets, weights, volatilities)
        sharpe_ratio = (portfolio_return - 0.02) / portfolio_volatility if portfolio_volatility > 0 else 0

        # Generate allocation details
        allocations = []
        for i, asset in enumerate(assets):
            allocation_amount = investment_amount * weights[i]
            allocations.append({
                "asset": asset,
                "weight": round(weights[i], 4),
                "amount": round(allocation_amount, 2),
                "expected_return": round(expected_returns[asset], 4),
                "volatility": round(volatilities[asset], 4)
            })

        # Sort by weight
        allocations.sort(key=lambda x: x["weight"], reverse=True)

        # Generate recommendations
        recommendations = await self._generate_recommendations(
            allocations, risk_tolerance, portfolio_return, portfolio_volatility
        )

        return {
            "portfolio_summary": {
                "total_investment": investment_amount,
                "expected_annual_return": round(portfolio_return, 4),
                "annual_volatility": round(portfolio_volatility, 4),
                "sharpe_ratio": round(sharpe_ratio, 4),
                "diversification_score": round(1 - max(weights), 4)
            },
            "allocations": allocations,
            "risk_metrics": {
                "value_at_risk_95": round(investment_amount * portfolio_volatility * 1.645, 2),
                "expected_shortfall": round(investment_amount * portfolio_volatility * 2.33, 2),
                "max_drawdown_estimate": round(portfolio_volatility * 2.5, 4)
            },
            "rebalancing": {
                "frequency": "quarterly",
                "threshold": 0.05,
                "next_review_date": "2024-12-31"
            },
            "recommendations": recommendations,
            "optimization_details": {
                "objective": objective,
                "risk_tolerance": risk_tolerance,
                "constraints": {
                    "max_single_position": 0.4,
                    "min_position_size": 0.01,
                    "target_assets": num_assets
                }
            }
        }

    def _generate_min_risk_weights(self, num_assets: int, diversification: float) -> List[float]:
        """Generate weights focused on risk minimization"""
        # Equal weight with slight randomization
        base_weight = 1.0 / num_assets
        weights = []

        for i in range(num_assets):
            # Add some randomness but keep well-diversified
            variation = random.uniform(-0.02, 0.02) * (1 - diversification)
            weight = max(0.01, base_weight + variation)
            weights.append(weight)

        return weights

    def _generate_max_return_weights(self, assets: List[str], expected_returns: Dict[str, float]) -> List[float]:
        """Generate weights focused on maximum returns"""
        # Sort assets by expected return
        sorted_assets = sorted(assets, key=lambda x: expected_returns[x], reverse=True)
        weights = [0.0] * len(assets)

        # Concentrate on top performers but maintain some diversification
        total_weight = 1.0
        for i, asset in enumerate(sorted_assets):
            asset_idx = assets.index(asset)
            if i < 3:  # Top 3 assets get more weight
                weight = total_weight * random.uniform(0.15, 0.25)
            elif i < 6:  # Next 3 assets get moderate weight
                weight = total_weight * random.uniform(0.08, 0.15)
            else:  # Remaining assets get small weight
                weight = total_weight * random.uniform(0.02, 0.08)

            weights[asset_idx] = weight
            total_weight -= weight

            if total_weight <= 0.1:
                break

        # Distribute remaining weight
        if total_weight > 0:
            for i in range(len(weights)):
                if weights[i] == 0:
                    weights[i] = total_weight / (len(weights) - sum(1 for w in weights if w > 0))

        return weights

    def _generate_sharpe_weights(self, num_assets: int, diversification: float) -> List[float]:
        """Generate weights focused on Sharpe ratio optimization"""
        # Balanced approach with some concentration
        weights = []
        remaining_weight = 1.0

        for i in range(num_assets):
            if i < num_assets - 1:
                # Gradually decreasing weights with randomness
                max_weight = min(0.3, remaining_weight * 0.6)
                min_weight = max(0.05, remaining_weight / (num_assets - i) * 0.5)
                weight = random.uniform(min_weight, max_weight)
                weights.append(weight)
                remaining_weight -= weight
            else:
                weights.append(remaining_weight)

        return weights

    def _calculate_portfolio_volatility(self, assets: List[str], weights: np.ndarray,
                                      volatilities: Dict[str, float]) -> float:
        """Calculate portfolio volatility (simplified)"""
        # Simplified calculation without correlation matrix
        weighted_variances = sum(
            (weights[i] * volatilities[asset]) ** 2
            for i, asset in enumerate(assets)
        )

        # Add estimated correlation effect (mock)
        avg_correlation = 0.3  # Assume 30% average correlation
        portfolio_variance = weighted_variances + avg_correlation * (1 - weighted_variances)

        return math.sqrt(max(0, portfolio_variance))

    async def _generate_recommendations(self, allocations: List[Dict], risk_tolerance: str,
                                      portfolio_return: float, portfolio_volatility: float) -> List[str]:
        """Generate portfolio recommendations"""
        recommendations = []

        # Check concentration
        max_weight = max(alloc["weight"] for alloc in allocations)
        if max_weight > 0.3:
            recommendations.append(f"Consider reducing concentration - largest position is {max_weight:.1%}")

        # Check diversification
        if len(allocations) < 5:
            recommendations.append("Consider adding more assets for better diversification")

        # Risk-specific recommendations
        if risk_tolerance == "conservative" and portfolio_volatility > 0.15:
            recommendations.append("Portfolio volatility may be too high for conservative risk tolerance")
        elif risk_tolerance == "aggressive" and portfolio_return < 0.10:
            recommendations.append("Expected return may be low for aggressive risk tolerance")

        # Asset-specific recommendations
        tech_weight = sum(
            alloc["weight"] for alloc in allocations
            if alloc["asset"] in ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA"]
        )
        if tech_weight > 0.4:
            recommendations.append("Consider reducing technology sector concentration")

        # Default recommendations
        if not recommendations:
            recommendations = [
                "Portfolio allocation appears well-balanced for your risk tolerance",
                "Consider regular rebalancing to maintain target allocations",
                "Review and adjust allocations based on market conditions"
            ]

        return recommendations[:5]  # Return top 5 recommendations