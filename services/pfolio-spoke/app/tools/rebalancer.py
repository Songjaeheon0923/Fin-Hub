"""
Rebalancer Tool - Analyze rebalancing needs
"""
import math
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List

from .base_tool import BaseTool


class Rebalancer(BaseTool):
    """Tool for analyzing portfolio rebalancing needs"""

    def __init__(self):
        super().__init__(
            tool_id="pfolio.rebalance_trigger",
            name="Rebalancing Trigger",
            description="리밸런싱 필요 여부를 확인합니다"
        )

    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute rebalancing analysis"""
        try:
            # Validate required arguments
            self.validate_arguments(arguments, ["current_portfolio", "target_portfolio"])

            current_portfolio = arguments["current_portfolio"]
            target_portfolio = arguments["target_portfolio"]
            threshold = arguments.get("threshold", 0.05)  # 5% default
            portfolio_value = arguments.get("portfolio_value", 100000)

            print(f"Analyzing rebalancing for portfolio value: ${portfolio_value:,.2f}")

            # Analyze rebalancing needs
            rebalancing_data = await self._analyze_rebalancing(
                current_portfolio, target_portfolio, threshold, portfolio_value
            )

            return self.create_success_response(
                data=rebalancing_data,
                metadata={
                    "portfolio_value": portfolio_value,
                    "rebalance_threshold": threshold,
                    "analysis_date": datetime.now().isoformat(),
                    "method": "threshold_based"
                }
            )

        except Exception as e:
            return await self.handle_error(e, "rebalancing_analysis")

    async def get_tool_info(self) -> Dict[str, Any]:
        """Get tool information for MCP schema"""
        return {
            "name": self.tool_id,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": {
                    "current_portfolio": {
                        "type": "object",
                        "description": "Current portfolio weights as asset:weight pairs",
                        "patternProperties": {
                            "^[A-Z]{2,5}$": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1
                            }
                        }
                    },
                    "target_portfolio": {
                        "type": "object",
                        "description": "Target portfolio weights as asset:weight pairs",
                        "patternProperties": {
                            "^[A-Z]{2,5}$": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1
                            }
                        }
                    },
                    "threshold": {
                        "type": "number",
                        "description": "Rebalancing threshold (0.05 = 5%)",
                        "minimum": 0.01,
                        "maximum": 0.2,
                        "default": 0.05
                    },
                    "portfolio_value": {
                        "type": "number",
                        "description": "Total portfolio value in USD",
                        "minimum": 1000,
                        "default": 100000
                    }
                },
                "required": ["current_portfolio", "target_portfolio"]
            }
        }

    async def _analyze_rebalancing(self, current: Dict[str, float], target: Dict[str, float],
                                 threshold: float, portfolio_value: float) -> Dict[str, Any]:
        """Analyze portfolio rebalancing needs"""

        # Calculate deviations
        all_assets = set(current.keys()) | set(target.keys())
        deviations = {}
        needs_rebalancing = False

        for asset in all_assets:
            current_weight = current.get(asset, 0.0)
            target_weight = target.get(asset, 0.0)
            deviation = current_weight - target_weight
            deviation_pct = abs(deviation)

            deviations[asset] = {
                "current_weight": current_weight,
                "target_weight": target_weight,
                "deviation": deviation,
                "deviation_pct": deviation_pct,
                "needs_rebalancing": deviation_pct > threshold
            }

            if deviation_pct > threshold:
                needs_rebalancing = True

        # Generate rebalancing actions
        actions = []
        total_buy = 0
        total_sell = 0

        for asset, dev in deviations.items():
            if dev["needs_rebalancing"]:
                current_value = dev["current_weight"] * portfolio_value
                target_value = dev["target_weight"] * portfolio_value
                trade_value = target_value - current_value

                action_type = "buy" if trade_value > 0 else "sell"
                trade_amount = abs(trade_value)

                actions.append({
                    "asset": asset,
                    "action": action_type,
                    "current_value": round(current_value, 2),
                    "target_value": round(target_value, 2),
                    "trade_amount": round(trade_amount, 2),
                    "current_weight": round(dev["current_weight"], 4),
                    "target_weight": round(dev["target_weight"], 4),
                    "deviation": round(dev["deviation"], 4)
                })

                if action_type == "buy":
                    total_buy += trade_amount
                else:
                    total_sell += trade_amount

        # Sort actions by trade amount
        actions.sort(key=lambda x: x["trade_amount"], reverse=True)

        # Calculate costs and impact
        transaction_costs = await self._calculate_transaction_costs(actions, portfolio_value)
        market_impact = await self._estimate_market_impact(actions)

        # Generate recommendations
        recommendations = await self._generate_rebalancing_recommendations(
            needs_rebalancing, deviations, actions, threshold
        )

        # Calculate next review date
        next_review = self._calculate_next_review()

        return {
            "rebalancing_summary": {
                "needs_rebalancing": needs_rebalancing,
                "assets_out_of_range": sum(1 for dev in deviations.values() if dev["needs_rebalancing"]),
                "total_assets": len(all_assets),
                "max_deviation": max(dev["deviation_pct"] for dev in deviations.values()),
                "threshold": threshold
            },
            "portfolio_analysis": {
                "current_total_weight": sum(current.values()),
                "target_total_weight": sum(target.values()),
                "portfolio_value": portfolio_value,
                "tracking_error": self._calculate_tracking_error(deviations)
            },
            "asset_analysis": [
                {
                    "asset": asset,
                    "current_weight": round(dev["current_weight"], 4),
                    "target_weight": round(dev["target_weight"], 4),
                    "deviation": round(dev["deviation"], 4),
                    "deviation_pct": round(dev["deviation_pct"], 4),
                    "status": "rebalance_needed" if dev["needs_rebalancing"] else "in_range",
                    "current_value": round(dev["current_weight"] * portfolio_value, 2),
                    "target_value": round(dev["target_weight"] * portfolio_value, 2)
                }
                for asset, dev in sorted(deviations.items(), key=lambda x: x[1]["deviation_pct"], reverse=True)
            ],
            "rebalancing_actions": actions,
            "trade_summary": {
                "total_buy_amount": round(total_buy, 2),
                "total_sell_amount": round(total_sell, 2),
                "net_trade_amount": round(abs(total_buy - total_sell), 2),
                "number_of_trades": len(actions)
            },
            "cost_analysis": transaction_costs,
            "market_impact": market_impact,
            "recommendations": recommendations,
            "timing": {
                "last_rebalance": (datetime.now() - timedelta(days=random.randint(30, 120))).strftime("%Y-%m-%d"),
                "next_review_date": next_review,
                "frequency": "quarterly"
            }
        }

    def _calculate_tracking_error(self, deviations: Dict[str, Dict]) -> float:
        """Calculate portfolio tracking error"""
        squared_deviations = sum(dev["deviation"] ** 2 for dev in deviations.values())
        return round(math.sqrt(squared_deviations / len(deviations)), 4)

    async def _calculate_transaction_costs(self, actions: List[Dict], portfolio_value: float) -> Dict[str, Any]:
        """Calculate estimated transaction costs"""
        # Mock transaction cost calculation
        total_trade_value = sum(action["trade_amount"] for action in actions)

        # Assume different cost structures
        commission_per_trade = 0.0  # Most brokers are commission-free now
        spread_cost_rate = 0.0005  # 0.05% spread cost

        spread_costs = total_trade_value * spread_cost_rate
        total_commissions = commission_per_trade * len(actions)
        total_costs = spread_costs + total_commissions

        cost_as_percentage = (total_costs / portfolio_value) if portfolio_value > 0 else 0

        return {
            "total_costs": round(total_costs, 2),
            "commission_costs": round(total_commissions, 2),
            "spread_costs": round(spread_costs, 2),
            "cost_as_percentage": round(cost_as_percentage, 4),
            "cost_per_trade": round(total_costs / len(actions), 2) if actions else 0,
            "break_even_days": round(total_costs / (portfolio_value * 0.0002), 0) if portfolio_value > 0 else 0  # Assume 0.02% daily return
        }

    async def _estimate_market_impact(self, actions: List[Dict]) -> Dict[str, Any]:
        """Estimate market impact of trades"""
        # Mock market impact estimation
        total_trade_value = sum(action["trade_amount"] for action in actions)

        # Assume small trades have minimal impact
        if total_trade_value < 50000:
            impact_level = "minimal"
            estimated_impact = 0.0001
        elif total_trade_value < 200000:
            impact_level = "low"
            estimated_impact = 0.0005
        elif total_trade_value < 1000000:
            impact_level = "moderate"
            estimated_impact = 0.002
        else:
            impact_level = "high"
            estimated_impact = 0.005

        return {
            "impact_level": impact_level,
            "estimated_impact_bps": round(estimated_impact * 10000, 1),  # basis points
            "estimated_cost": round(total_trade_value * estimated_impact, 2),
            "liquidity_assessment": "good" if impact_level in ["minimal", "low"] else "moderate",
            "recommended_execution": "market_order" if impact_level == "minimal" else "limit_order"
        }

    async def _generate_rebalancing_recommendations(self, needs_rebalancing: bool,
                                                  deviations: Dict, actions: List[Dict],
                                                  threshold: float) -> List[str]:
        """Generate rebalancing recommendations"""
        recommendations = []

        if not needs_rebalancing:
            recommendations.append("Portfolio is well-balanced within target thresholds")
            recommendations.append("No immediate rebalancing required")
            recommendations.append("Continue monitoring and review quarterly")
            return recommendations

        # Analyze deviations
        large_deviations = [
            asset for asset, dev in deviations.items()
            if dev["deviation_pct"] > threshold * 2
        ]

        if large_deviations:
            recommendations.append(f"Priority rebalancing needed for: {', '.join(large_deviations[:3])}")

        # Trade complexity
        if len(actions) > 10:
            recommendations.append("Consider phased rebalancing to reduce trade complexity")
        elif len(actions) <= 3:
            recommendations.append("Simple rebalancing - can be executed in single session")

        # Cost considerations
        total_trade_value = sum(action["trade_amount"] for action in actions)
        if total_trade_value < 1000:
            recommendations.append("Trade amounts are small - consider combining with next review")

        # Market timing
        recommendations.append("Consider market conditions and volatility before executing")
        recommendations.append("Use limit orders for larger trades to minimize market impact")

        # Specific action recommendations
        buy_actions = [a for a in actions if a["action"] == "buy"]
        sell_actions = [a for a in actions if a["action"] == "sell"]

        if len(buy_actions) > len(sell_actions):
            recommendations.append("More buying than selling required - ensure sufficient cash")
        elif len(sell_actions) > len(buy_actions):
            recommendations.append("More selling than buying - good for generating cash")

        return recommendations[:6]

    def _calculate_next_review(self) -> str:
        """Calculate next portfolio review date"""
        # Quarterly reviews
        next_review = datetime.now() + timedelta(days=90)
        return next_review.strftime("%Y-%m-%d")