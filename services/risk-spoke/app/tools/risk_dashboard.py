"""
Risk Dashboard Tool
Comprehensive risk analysis aggregating all risk metrics
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from .var_calculator import VaRCalculatorTool
from .risk_metrics import RiskMetricsTool
from .portfolio_risk import PortfolioRiskTool
from .stress_testing import StressTestingTool
from .tail_risk import TailRiskTool


class RiskDashboardTool:
    """Comprehensive risk dashboard aggregating all risk analyses"""

    def __init__(self):
        self.data_dir = Path(__file__).parent.parent.parent.parent.parent / "data" / "stock-data"

        # Initialize all risk tools
        self.var_tool = VaRCalculatorTool()
        self.metrics_tool = RiskMetricsTool()
        self.portfolio_tool = PortfolioRiskTool()
        self.stress_tool = StressTestingTool()
        self.tail_tool = TailRiskTool()

    async def get_tool_info(self) -> Dict:
        """Get tool information for MCP protocol"""
        return {
            "name": "risk.generate_dashboard",
            "description": "Generate comprehensive risk dashboard with all risk metrics and analyses",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "analysis_type": {
                        "type": "string",
                        "enum": ["single_asset", "portfolio"],
                        "description": "Type of risk analysis (default: single_asset)"
                    },
                    "symbol": {
                        "type": "string",
                        "description": "Stock symbol for single asset analysis"
                    },
                    "portfolio": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "symbol": {"type": "string"},
                                "weight": {"type": "number"}
                            }
                        },
                        "description": "Portfolio holdings for portfolio analysis"
                    },
                    "portfolio_value": {
                        "type": "number",
                        "description": "Total portfolio value in USD (default: 100000)"
                    },
                    "period": {
                        "type": "integer",
                        "description": "Analysis period in days (default: 252)"
                    },
                    "confidence_level": {
                        "type": "number",
                        "description": "VaR confidence level (default: 0.95)"
                    },
                    "risk_free_rate": {
                        "type": "number",
                        "description": "Risk-free rate (default: 0.04)"
                    },
                    "benchmark": {
                        "type": "string",
                        "description": "Benchmark symbol for comparison (default: SPY)"
                    },
                    "include_stress_test": {
                        "type": "boolean",
                        "description": "Include stress testing analysis (default: true)"
                    },
                    "include_tail_risk": {
                        "type": "boolean",
                        "description": "Include tail risk analysis (default: true)"
                    }
                },
                "required": []
            }
        }

    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute comprehensive risk dashboard generation"""
        try:
            analysis_type = arguments.get("analysis_type", "single_asset")
            symbol = arguments.get("symbol", "").upper()
            portfolio = arguments.get("portfolio")
            portfolio_value = arguments.get("portfolio_value", 100000)
            period = arguments.get("period", 252)
            confidence_level = arguments.get("confidence_level", 0.95)
            risk_free_rate = arguments.get("risk_free_rate", 0.04)
            benchmark = arguments.get("benchmark", "SPY")
            include_stress = arguments.get("include_stress_test", True)
            include_tail = arguments.get("include_tail_risk", True)

            # Validate inputs
            if analysis_type == "single_asset":
                if not symbol:
                    return {"error": "Symbol required for single asset analysis"}
                return await self._generate_single_asset_dashboard(
                    symbol, portfolio_value, period, confidence_level,
                    risk_free_rate, benchmark, include_stress, include_tail
                )
            elif analysis_type == "portfolio":
                if not portfolio:
                    return {"error": "Portfolio required for portfolio analysis"}
                return await self._generate_portfolio_dashboard(
                    portfolio, portfolio_value, period, confidence_level,
                    risk_free_rate, include_stress, include_tail
                )
            else:
                return {"error": f"Invalid analysis type: {analysis_type}"}

        except Exception as e:
            return {"error": f"Dashboard generation failed: {str(e)}"}

    async def _generate_single_asset_dashboard(
        self,
        symbol: str,
        portfolio_value: float,
        period: int,
        confidence_level: float,
        risk_free_rate: float,
        benchmark: str,
        include_stress: bool,
        include_tail: bool
    ) -> Dict:
        """Generate comprehensive dashboard for single asset"""

        dashboard = {
            "dashboard_type": "single_asset",
            "symbol": symbol,
            "portfolio_value": portfolio_value,
            "analysis_timestamp": datetime.now().isoformat(),
            "period_days": period,
            "confidence_level": confidence_level
        }

        # 1. VaR Analysis
        var_result = await self.var_tool.execute({
            "symbol": symbol,
            "method": "all",
            "confidence_level": confidence_level,
            "portfolio_value": portfolio_value,
            "period": period
        })

        if "error" not in var_result:
            dashboard["var_analysis"] = {
                "methods": var_result.get("methods", {}),
                "recommendation": var_result.get("recommendation", ""),
                "risk_level": var_result.get("risk_assessment", {}).get("overall_risk_level", "UNKNOWN")
            }

        # 2. Risk Metrics
        metrics_result = await self.metrics_tool.execute({
            "symbol": symbol,
            "metrics": ["all"],
            "period": period,
            "risk_free_rate": risk_free_rate,
            "benchmark": benchmark
        })

        if "error" not in metrics_result:
            dashboard["risk_metrics"] = {
                "sharpe_ratio": metrics_result.get("metrics", {}).get("sharpe_ratio", {}),
                "sortino_ratio": metrics_result.get("metrics", {}).get("sortino_ratio", {}),
                "max_drawdown": metrics_result.get("metrics", {}).get("max_drawdown", {}),
                "volatility": metrics_result.get("metrics", {}).get("volatility", {}),
                "returns": metrics_result.get("metrics", {}).get("returns", {}),
                "summary": metrics_result.get("summary", {})
            }

        # 3. Stress Testing
        if include_stress:
            stress_result = await self.stress_tool.execute({
                "symbol": symbol,
                "scenarios": ["2008_financial_crisis", "2020_covid_crash"],
                "portfolio_value": portfolio_value
            })

            if "error" not in stress_result:
                dashboard["stress_testing"] = {
                    "scenarios": stress_result.get("scenarios", {}),
                    "worst_case": stress_result.get("worst_case_scenario", {}),
                    "recommendations": stress_result.get("recommendations", [])
                }

        # 4. Tail Risk Analysis
        if include_tail:
            tail_result = await self.tail_tool.execute({
                "symbol": symbol,
                "period": min(period * 2, 1000),  # Use longer period for tail risk
                "analysis": ["all"]
            })

            if "error" not in tail_result:
                dashboard["tail_risk"] = {
                    "extreme_value_theory": tail_result.get("analyses", {}).get("extreme_value_theory", {}),
                    "fat_tail": tail_result.get("analyses", {}).get("fat_tail", {}),
                    "black_swan": tail_result.get("analyses", {}).get("black_swan", {}),
                    "assessment": tail_result.get("assessment", {})
                }

        # 5. Overall Risk Assessment
        dashboard["overall_assessment"] = self._generate_overall_assessment(dashboard)

        # 6. Risk Score Card
        dashboard["risk_scorecard"] = self._generate_risk_scorecard(dashboard)

        # 7. Recommendations
        dashboard["recommendations"] = self._generate_recommendations(dashboard)

        # 8. Key Risk Indicators (KRIs)
        dashboard["key_risk_indicators"] = self._extract_key_risk_indicators(dashboard)

        return dashboard

    async def _generate_portfolio_dashboard(
        self,
        portfolio: List[Dict],
        portfolio_value: float,
        period: int,
        confidence_level: float,
        risk_free_rate: float,
        include_stress: bool,
        include_tail: bool
    ) -> Dict:
        """Generate comprehensive dashboard for portfolio"""

        dashboard = {
            "dashboard_type": "portfolio",
            "portfolio_size": len(portfolio),
            "portfolio_value": portfolio_value,
            "analysis_timestamp": datetime.now().isoformat(),
            "period_days": period,
            "confidence_level": confidence_level
        }

        # 1. Portfolio Risk Analysis
        portfolio_result = await self.portfolio_tool.execute({
            "portfolio": portfolio,
            "period": period,
            "confidence_level": confidence_level,
            "risk_free_rate": risk_free_rate
        })

        if "error" not in portfolio_result:
            dashboard["portfolio_metrics"] = {
                "returns": portfolio_result.get("metrics", {}).get("returns", {}),
                "risk": portfolio_result.get("metrics", {}).get("risk", {}),
                "var": portfolio_result.get("metrics", {}).get("var", {}),
                "diversification": portfolio_result.get("metrics", {}).get("diversification", {}),
                "concentration": portfolio_result.get("metrics", {}).get("concentration", {}),
                "performance": portfolio_result.get("metrics", {}).get("performance", {})
            }

        # 2. Individual Asset Metrics (for top holdings)
        top_holdings = sorted(portfolio, key=lambda x: x["weight"], reverse=True)[:3]
        dashboard["top_holdings_analysis"] = []

        for holding in top_holdings:
            symbol = holding["symbol"]
            weight = holding["weight"]

            # Get VaR for each holding
            var_result = await self.var_tool.execute({
                "symbol": symbol,
                "method": "historical",
                "confidence_level": confidence_level,
                "portfolio_value": portfolio_value * weight,
                "period": period
            })

            # Get risk metrics for each holding
            metrics_result = await self.metrics_tool.execute({
                "symbol": symbol,
                "metrics": ["sharpe", "volatility", "drawdown"],
                "period": period,
                "risk_free_rate": risk_free_rate
            })

            holding_analysis = {
                "symbol": symbol,
                "weight_percent": weight * 100,
                "value": portfolio_value * weight,
                "var": var_result.get("methods", {}).get("historical", {}) if "error" not in var_result else None,
                "metrics": {
                    "sharpe": metrics_result.get("metrics", {}).get("sharpe_ratio", {}) if "error" not in metrics_result else None,
                    "volatility": metrics_result.get("metrics", {}).get("volatility", {}) if "error" not in metrics_result else None,
                    "max_drawdown": metrics_result.get("metrics", {}).get("max_drawdown", {}) if "error" not in metrics_result else None
                }
            }
            dashboard["top_holdings_analysis"].append(holding_analysis)

        # 3. Portfolio Stress Testing
        if include_stress:
            # Stress test the entire portfolio
            stress_results = []
            for scenario in ["2008_financial_crisis", "2020_covid_crash"]:
                scenario_impact = {"scenario": scenario, "holdings_impact": []}

                for holding in portfolio:
                    stress_result = await self.stress_tool.execute({
                        "symbol": holding["symbol"],
                        "scenarios": [scenario],
                        "portfolio_value": portfolio_value * holding["weight"]
                    })

                    if "error" not in stress_result and "scenarios" in stress_result:
                        scenario_data = stress_result["scenarios"].get(scenario, {})
                        scenario_impact["holdings_impact"].append({
                            "symbol": holding["symbol"],
                            "weight": holding["weight"],
                            "impact": scenario_data.get("final_value", 0) - (portfolio_value * holding["weight"])
                        })

                # Calculate total portfolio impact
                total_impact = sum(h["impact"] for h in scenario_impact["holdings_impact"])
                scenario_impact["total_impact"] = total_impact
                scenario_impact["impact_percent"] = (total_impact / portfolio_value) * 100
                stress_results.append(scenario_impact)

            dashboard["stress_testing"] = {
                "scenarios": stress_results,
                "worst_case_loss": min(s["impact_percent"] for s in stress_results) if stress_results else 0
            }

        # 4. Tail Risk (for largest holding)
        if include_tail and portfolio:
            largest_holding = max(portfolio, key=lambda x: x["weight"])
            tail_result = await self.tail_tool.execute({
                "symbol": largest_holding["symbol"],
                "period": min(period * 2, 1000),
                "analysis": ["all"]
            })

            if "error" not in tail_result:
                dashboard["tail_risk"] = {
                    "analyzed_symbol": largest_holding["symbol"],
                    "weight_percent": largest_holding["weight"] * 100,
                    "assessment": tail_result.get("assessment", {}),
                    "note": "Tail risk analyzed for largest holding as proxy"
                }

        # 5. Overall Risk Assessment
        dashboard["overall_assessment"] = self._generate_overall_assessment(dashboard)

        # 6. Risk Score Card
        dashboard["risk_scorecard"] = self._generate_risk_scorecard(dashboard)

        # 7. Recommendations
        dashboard["recommendations"] = self._generate_recommendations(dashboard)

        # 8. Key Risk Indicators (KRIs)
        dashboard["key_risk_indicators"] = self._extract_key_risk_indicators(dashboard)

        return dashboard

    def _generate_overall_assessment(self, dashboard: Dict) -> Dict:
        """Generate overall risk assessment from all analyses"""

        risk_scores = []
        risk_factors = []

        # VaR Risk Score
        if "var_analysis" in dashboard:
            var_risk = dashboard["var_analysis"].get("risk_level", "UNKNOWN")
            if var_risk == "CRITICAL":
                risk_scores.append(100)
                risk_factors.append("CRITICAL: Extreme VaR levels")
            elif var_risk == "HIGH":
                risk_scores.append(75)
                risk_factors.append("HIGH: Elevated VaR risk")
            elif var_risk == "MODERATE":
                risk_scores.append(50)
            elif var_risk == "LOW":
                risk_scores.append(25)

        # Risk Metrics Score
        if "risk_metrics" in dashboard:
            sharpe = dashboard["risk_metrics"].get("sharpe_ratio", {}).get("value", 0)
            vol = dashboard["risk_metrics"].get("volatility", {}).get("annual_percent", 0)
            dd = dashboard["risk_metrics"].get("max_drawdown", {}).get("max_drawdown_percent", 0)

            # Sharpe score (inverted - lower is riskier)
            if sharpe < 0:
                risk_scores.append(80)
                risk_factors.append("Negative risk-adjusted returns")
            elif sharpe < 1:
                risk_scores.append(60)
            elif sharpe < 2:
                risk_scores.append(30)
            else:
                risk_scores.append(10)

            # Volatility score
            if vol > 60:
                risk_scores.append(90)
                risk_factors.append("Extremely high volatility")
            elif vol > 40:
                risk_scores.append(70)
                risk_factors.append("High volatility")
            elif vol > 25:
                risk_scores.append(40)
            else:
                risk_scores.append(20)

            # Drawdown score
            if abs(dd) > 50:
                risk_scores.append(90)
                risk_factors.append("Severe historical drawdowns")
            elif abs(dd) > 30:
                risk_scores.append(70)
                risk_factors.append("Significant drawdown risk")
            elif abs(dd) > 20:
                risk_scores.append(40)
            else:
                risk_scores.append(20)

        # Tail Risk Score
        if "tail_risk" in dashboard:
            tail_score = dashboard["tail_risk"].get("assessment", {}).get("tail_risk_score", 0)
            risk_scores.append(tail_score)

            if tail_score > 70:
                risk_factors.append("CRITICAL: Black swan risk detected")
            elif tail_score > 50:
                risk_factors.append("HIGH: Significant tail risk")

        # Stress Test Score
        if "stress_testing" in dashboard:
            if dashboard["dashboard_type"] == "single_asset":
                worst_case = dashboard["stress_testing"].get("worst_case", {})
                loss_pct = abs(worst_case.get("loss_percent", 0))
            else:
                loss_pct = abs(dashboard["stress_testing"].get("worst_case_loss", 0))

            if loss_pct > 50:
                risk_scores.append(90)
                risk_factors.append("Extreme stress test losses")
            elif loss_pct > 30:
                risk_scores.append(70)
                risk_factors.append("High stress test vulnerability")
            elif loss_pct > 15:
                risk_scores.append(40)
            else:
                risk_scores.append(20)

        # Calculate overall risk score
        overall_risk_score = sum(risk_scores) / len(risk_scores) if risk_scores else 50

        # Determine risk level
        if overall_risk_score >= 75:
            risk_level = "CRITICAL"
            status = "Immediate risk reduction required"
        elif overall_risk_score >= 60:
            risk_level = "HIGH"
            status = "Elevated risk - consider hedging"
        elif overall_risk_score >= 40:
            risk_level = "MODERATE"
            status = "Manageable risk with monitoring"
        elif overall_risk_score >= 25:
            risk_level = "LOW"
            status = "Acceptable risk level"
        else:
            risk_level = "MINIMAL"
            status = "Low risk profile"

        return {
            "overall_risk_score": round(overall_risk_score, 2),
            "risk_level": risk_level,
            "status": status,
            "primary_risk_factors": risk_factors if risk_factors else ["No significant risks identified"],
            "risk_components": {
                "var_risk": risk_scores[0] if len(risk_scores) > 0 else None,
                "volatility_risk": risk_scores[2] if len(risk_scores) > 2 else None,
                "tail_risk": next((s for i, s in enumerate(risk_scores) if "tail_risk" in dashboard), None),
                "stress_risk": risk_scores[-1] if "stress_testing" in dashboard else None
            }
        }

    def _generate_risk_scorecard(self, dashboard: Dict) -> Dict:
        """Generate risk scorecard with key metrics"""

        scorecard = {}

        # Market Risk
        if "var_analysis" in dashboard:
            var_95 = dashboard["var_analysis"].get("methods", {}).get("historical", {}).get("var_usd", 0)
            scorecard["market_risk"] = {
                "var_95_percent": var_95,
                "rating": self._rate_metric(var_95, [5000, 10000, 20000, 50000], reverse=True)
            }

        # Volatility Risk
        if "risk_metrics" in dashboard:
            vol = dashboard["risk_metrics"].get("volatility", {}).get("annual_percent", 0)
            scorecard["volatility_risk"] = {
                "annual_volatility_percent": vol,
                "rating": self._rate_metric(vol, [20, 30, 50, 70], reverse=True)
            }

        # Performance Risk
        if "risk_metrics" in dashboard:
            sharpe = dashboard["risk_metrics"].get("sharpe_ratio", {}).get("value", 0)
            scorecard["performance_risk"] = {
                "sharpe_ratio": sharpe,
                "rating": self._rate_metric(sharpe, [0, 0.5, 1.0, 2.0], reverse=False)
            }

        # Drawdown Risk
        if "risk_metrics" in dashboard:
            dd = abs(dashboard["risk_metrics"].get("max_drawdown", {}).get("max_drawdown_percent", 0))
            scorecard["drawdown_risk"] = {
                "max_drawdown_percent": dd,
                "rating": self._rate_metric(dd, [10, 20, 35, 50], reverse=True)
            }

        # Tail Risk
        if "tail_risk" in dashboard:
            tail_score = dashboard["tail_risk"].get("assessment", {}).get("tail_risk_score", 0)
            scorecard["tail_risk"] = {
                "tail_risk_score": tail_score,
                "rating": self._rate_metric(tail_score, [20, 40, 60, 80], reverse=True)
            }

        # Diversification (portfolio only)
        if "portfolio_metrics" in dashboard:
            div_ratio = dashboard["portfolio_metrics"].get("diversification", {}).get("diversification_ratio", 1)
            scorecard["diversification"] = {
                "diversification_ratio": div_ratio,
                "rating": self._rate_metric(div_ratio, [1.0, 1.2, 1.4, 1.6], reverse=False)
            }

        return scorecard

    def _rate_metric(self, value: float, thresholds: List[float], reverse: bool = False) -> str:
        """Rate a metric on A-F scale"""
        if reverse:
            # Lower is better
            if value < thresholds[0]:
                return "A"
            elif value < thresholds[1]:
                return "B"
            elif value < thresholds[2]:
                return "C"
            elif value < thresholds[3]:
                return "D"
            else:
                return "F"
        else:
            # Higher is better
            if value > thresholds[3]:
                return "A"
            elif value > thresholds[2]:
                return "B"
            elif value > thresholds[1]:
                return "C"
            elif value > thresholds[0]:
                return "D"
            else:
                return "F"

    def _generate_recommendations(self, dashboard: Dict) -> List[str]:
        """Generate actionable recommendations"""

        recommendations = []

        # Overall risk assessment recommendations
        overall = dashboard.get("overall_assessment", {})
        risk_level = overall.get("risk_level", "UNKNOWN")

        if risk_level == "CRITICAL":
            recommendations.append("🚨 URGENT: Reduce position sizes immediately")
            recommendations.append("Implement protective puts or collar strategies")
            recommendations.append("Consider raising cash reserves to 30-50%")
        elif risk_level == "HIGH":
            recommendations.append("Consider hedging with options or inverse ETFs")
            recommendations.append("Reduce exposure to high-volatility assets")
            recommendations.append("Implement stop-loss orders")

        # VaR-based recommendations
        if "var_analysis" in dashboard:
            var_risk = dashboard["var_analysis"].get("risk_level", "")
            if var_risk in ["HIGH", "CRITICAL"]:
                recommendations.append("VaR levels elevated - consider position sizing reduction")

        # Volatility recommendations
        if "risk_metrics" in dashboard:
            vol = dashboard["risk_metrics"].get("volatility", {}).get("annual_percent", 0)
            if vol > 50:
                recommendations.append(f"High volatility ({vol:.1f}%) - consider volatility-selling strategies")

        # Sharpe ratio recommendations
        if "risk_metrics" in dashboard:
            sharpe = dashboard["risk_metrics"].get("sharpe_ratio", {}).get("value", 0)
            if sharpe < 0:
                recommendations.append("Negative risk-adjusted returns - review investment thesis")
            elif sharpe < 1:
                recommendations.append("Low Sharpe ratio - seek better risk-adjusted alternatives")

        # Tail risk recommendations
        if "tail_risk" in dashboard:
            tail_recs = dashboard["tail_risk"].get("assessment", {}).get("recommendations", [])
            recommendations.extend(tail_recs[:2])  # Add top 2 tail risk recommendations

        # Stress test recommendations
        if "stress_testing" in dashboard:
            stress_recs = dashboard["stress_testing"].get("recommendations", [])
            recommendations.extend(stress_recs[:2])  # Add top 2 stress test recommendations

        # Portfolio-specific recommendations
        if "portfolio_metrics" in dashboard:
            conc = dashboard["portfolio_metrics"].get("concentration", {})
            hhi = conc.get("herfindahl_index", 0)
            if hhi > 0.3:
                recommendations.append("High concentration risk - increase diversification")

            div_ratio = dashboard["portfolio_metrics"].get("diversification", {}).get("diversification_ratio", 1)
            if div_ratio < 1.2:
                recommendations.append("Low diversification benefit - add uncorrelated assets")

        # Remove duplicates and limit to top 10
        recommendations = list(dict.fromkeys(recommendations))[:10]

        if not recommendations:
            recommendations.append("Risk levels within acceptable range")
            recommendations.append("Continue regular monitoring")

        return recommendations

    def _extract_key_risk_indicators(self, dashboard: Dict) -> Dict:
        """Extract key risk indicators for quick reference"""

        kris = {}

        # VaR
        if "var_analysis" in dashboard:
            var_95 = dashboard["var_analysis"].get("methods", {}).get("historical", {}).get("var_usd", 0)
            kris["value_at_risk_95"] = round(var_95, 2)

        # Volatility
        if "risk_metrics" in dashboard:
            vol = dashboard["risk_metrics"].get("volatility", {}).get("annual_percent", 0)
            kris["annual_volatility"] = round(vol, 2)

        # Sharpe Ratio
        if "risk_metrics" in dashboard:
            sharpe = dashboard["risk_metrics"].get("sharpe_ratio", {}).get("value", 0)
            kris["sharpe_ratio"] = round(sharpe, 3)

        # Max Drawdown
        if "risk_metrics" in dashboard:
            dd = dashboard["risk_metrics"].get("max_drawdown", {}).get("max_drawdown_percent", 0)
            kris["max_drawdown_percent"] = round(dd, 2)

        # Tail Risk Score
        if "tail_risk" in dashboard:
            tail_score = dashboard["tail_risk"].get("assessment", {}).get("tail_risk_score", 0)
            kris["tail_risk_score"] = round(tail_score, 2)

        # Portfolio-specific KRIs
        if "portfolio_metrics" in dashboard:
            div_ratio = dashboard["portfolio_metrics"].get("diversification", {}).get("diversification_ratio", 0)
            kris["diversification_ratio"] = round(div_ratio, 3)

            hhi = dashboard["portfolio_metrics"].get("concentration", {}).get("herfindahl_index", 0)
            kris["concentration_hhi"] = round(hhi, 4)

        return kris
