"""
Stress Testing Tool
Simulates portfolio performance under extreme market conditions
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from scipy import stats


class StressTestingTool:
    """Advanced stress testing with historical and custom scenarios"""

    def __init__(self):
        self.data_dir = Path(__file__).parent.parent.parent.parent.parent / "data" / "stock-data"

        # Historical crisis scenarios (based on actual market data)
        self.crisis_scenarios = {
            "2008_financial_crisis": {
                "name": "2008 Global Financial Crisis",
                "period": "Sep 2008 - Mar 2009",
                "market_drop": -0.57,  # S&P 500 dropped 57%
                "volatility_increase": 3.5,  # VIX increased 3.5x
                "duration_days": 180,
                "description": "Lehman Brothers collapse, credit crisis, housing bubble burst"
            },
            "2020_covid_crash": {
                "name": "2020 COVID-19 Pandemic Crash",
                "period": "Feb 2020 - Mar 2020",
                "market_drop": -0.34,  # S&P 500 dropped 34%
                "volatility_increase": 4.0,  # VIX spiked to 80+
                "duration_days": 33,
                "description": "Global pandemic, lockdowns, economic shutdown"
            },
            "2022_inflation_shock": {
                "name": "2022 Inflation & Rate Hike Shock",
                "period": "Jan 2022 - Oct 2022",
                "market_drop": -0.25,  # S&P 500 dropped 25%
                "volatility_increase": 1.8,
                "duration_days": 280,
                "description": "Aggressive Fed rate hikes, high inflation, recession fears"
            },
            "2015_china_crash": {
                "name": "2015 China Stock Market Crash",
                "period": "Jun 2015 - Aug 2015",
                "market_drop": -0.43,  # Shanghai dropped 43%
                "volatility_increase": 2.2,
                "duration_days": 90,
                "description": "Chinese stock market bubble burst, currency devaluation"
            },
            "2011_euro_crisis": {
                "name": "2011 European Debt Crisis",
                "period": "Jul 2011 - Oct 2011",
                "market_drop": -0.19,  # S&P 500 dropped 19%
                "volatility_increase": 2.5,
                "duration_days": 105,
                "description": "Greek debt crisis, eurozone instability"
            }
        }

    async def get_tool_info(self) -> Dict:
        """Get tool information for MCP protocol"""
        return {
            "name": "risk_stress_test",
            "description": "Perform stress testing on portfolio under extreme market scenarios",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "portfolio": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "symbol": {"type": "string"},
                                "weight": {"type": "number"}
                            }
                        },
                        "description": "Portfolio composition (for portfolio stress test)"
                    },
                    "symbol": {
                        "type": "string",
                        "description": "Single stock symbol (for single asset stress test)"
                    },
                    "scenarios": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Scenarios to test: 2008_financial_crisis, 2020_covid_crash, 2022_inflation_shock, 2015_china_crash, 2011_euro_crisis, custom, worst_case, all"
                    },
                    "custom_scenario": {
                        "type": "object",
                        "properties": {
                            "market_drop": {"type": "number"},
                            "volatility_increase": {"type": "number"},
                            "duration_days": {"type": "integer"}
                        },
                        "description": "Custom scenario parameters"
                    },
                    "simulations": {
                        "type": "integer",
                        "description": "Number of Monte Carlo simulations (default: 10000)"
                    },
                    "confidence_level": {
                        "type": "number",
                        "description": "Confidence level for stress VaR (default: 0.99)"
                    }
                },
                "required": []
            }
        }

    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute stress testing"""
        try:
            portfolio = arguments.get("portfolio")
            symbol = arguments.get("symbol")
            scenarios = arguments.get("scenarios", ["all"])
            custom_scenario = arguments.get("custom_scenario")
            simulations = arguments.get("simulations", 10000)
            confidence = arguments.get("confidence_level", 0.99)

            # Determine if portfolio or single asset
            if portfolio:
                return await self._stress_test_portfolio(
                    portfolio, scenarios, custom_scenario, simulations, confidence
                )
            elif symbol:
                return await self._stress_test_asset(
                    symbol, scenarios, custom_scenario, simulations, confidence
                )
            else:
                return {"error": "Either portfolio or symbol must be provided"}

        except Exception as e:
            return {"error": f"Stress testing failed: {str(e)}"}

    async def _stress_test_asset(
        self, symbol: str, scenarios: List[str], custom_scenario: Optional[Dict],
        simulations: int, confidence: float
    ) -> Dict:
        """Stress test a single asset"""
        symbol = symbol.upper()

        # Load asset data
        data_file = self.data_dir / f"{symbol}.csv"
        if not data_file.exists():
            return {"error": f"No data available for {symbol}"}

        df = pd.read_csv(data_file, index_col=0, parse_dates=True)
        if df.empty or 'Close' not in df.columns:
            return {"error": f"Invalid data for {symbol}"}

        # Get recent data for baseline
        df = df.tail(500)
        returns = df['Close'].pct_change().dropna()

        result = {
            "symbol": symbol,
            "current_price": round(df['Close'].iloc[-1], 2),
            "baseline_volatility": round(returns.std() * np.sqrt(252) * 100, 2),
            "baseline_var_99": round(abs(np.percentile(returns, 1)) * 100, 4),
            "scenarios": {}
        }

        # Determine which scenarios to run
        scenario_list = []
        if "all" in scenarios:
            scenario_list = list(self.crisis_scenarios.keys())
            if custom_scenario:
                scenario_list.append("custom")
            scenario_list.append("worst_case")
        else:
            scenario_list = scenarios

        # Run each scenario
        for scenario_name in scenario_list:
            if scenario_name == "custom" and custom_scenario:
                result["scenarios"]["custom"] = self._apply_custom_scenario(
                    returns, custom_scenario
                )
            elif scenario_name == "worst_case":
                result["scenarios"]["worst_case"] = self._worst_case_scenario(
                    returns, simulations
                )
            elif scenario_name in self.crisis_scenarios:
                result["scenarios"][scenario_name] = self._apply_historical_scenario(
                    returns, self.crisis_scenarios[scenario_name], df['Close'].iloc[-1]
                )

        # Add overall assessment
        result["assessment"] = self._generate_assessment(result["scenarios"])

        # Add worst case scenario details for easy access
        worst_name = result["assessment"].get("worst_scenario")
        if worst_name and worst_name in result["scenarios"]:
            result["worst_case_scenario"] = {
                "scenario_name": worst_name,
                **result["scenarios"][worst_name]
            }

        return result

    async def _stress_test_portfolio(
        self, portfolio: List[Dict], scenarios: List[str], custom_scenario: Optional[Dict],
        simulations: int, confidence: float
    ) -> Dict:
        """Stress test a portfolio"""
        # Extract symbols and weights
        symbols = [p.get("symbol", "").upper() for p in portfolio]
        weights = np.array([p.get("weight", 0) for p in portfolio])

        # Validate
        if not np.isclose(weights.sum(), 1.0, atol=0.01):
            return {"error": f"Weights must sum to 1.0 (currently: {weights.sum()})"}

        # Load data for all assets
        price_data = {}
        for symbol in symbols:
            data_file = self.data_dir / f"{symbol}.csv"
            if not data_file.exists():
                return {"error": f"No data available for {symbol}"}

            df = pd.read_csv(data_file, index_col=0, parse_dates=True)
            if df.empty or 'Close' not in df.columns:
                return {"error": f"Invalid data for {symbol}"}

            price_data[symbol] = df['Close'].tail(500)

        # Create aligned price matrix
        price_df = pd.DataFrame(price_data).dropna()
        if len(price_df) < 30:
            return {"error": "Insufficient overlapping data"}

        # Calculate returns matrix
        returns_df = price_df.pct_change().dropna()

        # Portfolio returns
        portfolio_returns = (returns_df * weights).sum(axis=1)

        result = {
            "portfolio": portfolio,
            "baseline_volatility": round(portfolio_returns.std() * np.sqrt(252) * 100, 2),
            "baseline_var_99": round(abs(np.percentile(portfolio_returns, 1)) * 100, 4),
            "scenarios": {}
        }

        # Determine scenarios
        scenario_list = []
        if "all" in scenarios:
            scenario_list = list(self.crisis_scenarios.keys())
            if custom_scenario:
                scenario_list.append("custom")
            scenario_list.append("worst_case")
        else:
            scenario_list = scenarios

        # Run scenarios
        for scenario_name in scenario_list:
            if scenario_name == "custom" and custom_scenario:
                result["scenarios"]["custom"] = self._apply_custom_scenario_portfolio(
                    returns_df, weights, custom_scenario
                )
            elif scenario_name == "worst_case":
                result["scenarios"]["worst_case"] = self._worst_case_scenario_portfolio(
                    returns_df, weights, simulations
                )
            elif scenario_name in self.crisis_scenarios:
                result["scenarios"][scenario_name] = self._apply_historical_scenario_portfolio(
                    returns_df, weights, self.crisis_scenarios[scenario_name]
                )

        # Overall assessment
        result["assessment"] = self._generate_assessment(result["scenarios"])

        # Add worst case scenario details for easy access
        worst_name = result["assessment"].get("worst_scenario")
        if worst_name and worst_name in result["scenarios"]:
            result["worst_case_scenario"] = {
                "scenario_name": worst_name,
                **result["scenarios"][worst_name]
            }

        return result

    def _apply_historical_scenario(
        self, returns: pd.Series, scenario: Dict, current_price: float
    ) -> Dict:
        """Apply historical crisis scenario to single asset"""
        # Calculate stressed returns based on scenario
        market_drop = scenario["market_drop"]
        vol_increase = scenario["volatility_increase"]
        duration = scenario["duration_days"]

        # Current statistics
        mean_return = returns.mean()
        std_return = returns.std()

        # Stressed statistics
        stressed_mean = mean_return + (market_drop / duration)  # Daily drop rate
        stressed_std = std_return * vol_increase

        # Simulate stressed returns
        np.random.seed(42)
        stressed_returns = np.random.normal(stressed_mean, stressed_std, duration)

        # Calculate outcomes
        cumulative_return = (1 + stressed_returns).prod() - 1
        final_price = current_price * (1 + cumulative_return)
        loss = cumulative_return * 100

        # VaR and CVaR under stress
        var_stress = np.percentile(stressed_returns, 1) * 100
        cvar_stress = stressed_returns[stressed_returns <= np.percentile(stressed_returns, 1)].mean() * 100

        return {
            "name": scenario["name"],
            "period": scenario["period"],
            "description": scenario["description"],
            "expected_loss_percent": round(loss, 2),
            "expected_price": round(final_price, 2),
            "stressed_volatility": round(stressed_std * np.sqrt(252) * 100, 2),
            "stressed_var_99": round(abs(var_stress), 4),
            "stressed_cvar_99": round(abs(cvar_stress), 4),
            "duration_days": duration,
            "severity": self._assess_severity(loss)
        }

    def _apply_historical_scenario_portfolio(
        self, returns_df: pd.DataFrame, weights: np.ndarray, scenario: Dict
    ) -> Dict:
        """Apply historical scenario to portfolio"""
        market_drop = scenario["market_drop"]
        vol_increase = scenario["volatility_increase"]
        duration = scenario["duration_days"]

        # Portfolio statistics
        portfolio_returns = (returns_df * weights).sum(axis=1)
        mean_return = portfolio_returns.mean()
        std_return = portfolio_returns.std()

        # Stressed parameters
        stressed_mean = mean_return + (market_drop / duration)
        stressed_std = std_return * vol_increase

        # Simulate
        np.random.seed(42)
        stressed_returns = np.random.normal(stressed_mean, stressed_std, duration)

        cumulative_return = (1 + stressed_returns).prod() - 1
        loss = cumulative_return * 100

        var_stress = np.percentile(stressed_returns, 1) * 100
        cvar_stress = stressed_returns[stressed_returns <= np.percentile(stressed_returns, 1)].mean() * 100

        return {
            "name": scenario["name"],
            "period": scenario["period"],
            "description": scenario["description"],
            "expected_loss_percent": round(loss, 2),
            "stressed_volatility": round(stressed_std * np.sqrt(252) * 100, 2),
            "stressed_var_99": round(abs(var_stress), 4),
            "stressed_cvar_99": round(abs(cvar_stress), 4),
            "duration_days": duration,
            "severity": self._assess_severity(loss)
        }

    def _apply_custom_scenario(self, returns: pd.Series, scenario: Dict) -> Dict:
        """Apply custom stress scenario"""
        market_drop = scenario.get("market_drop", -0.3)
        vol_increase = scenario.get("volatility_increase", 2.0)
        duration = scenario.get("duration_days", 60)

        mean_return = returns.mean()
        std_return = returns.std()

        stressed_mean = mean_return + (market_drop / duration)
        stressed_std = std_return * vol_increase

        np.random.seed(42)
        stressed_returns = np.random.normal(stressed_mean, stressed_std, duration)

        cumulative_return = (1 + stressed_returns).prod() - 1
        loss = cumulative_return * 100

        return {
            "name": "Custom Scenario",
            "parameters": {
                "market_drop_percent": round(market_drop * 100, 2),
                "volatility_multiplier": vol_increase,
                "duration_days": duration
            },
            "expected_loss_percent": round(loss, 2),
            "stressed_volatility": round(stressed_std * np.sqrt(252) * 100, 2),
            "severity": self._assess_severity(loss)
        }

    def _apply_custom_scenario_portfolio(
        self, returns_df: pd.DataFrame, weights: np.ndarray, scenario: Dict
    ) -> Dict:
        """Apply custom scenario to portfolio"""
        market_drop = scenario.get("market_drop", -0.3)
        vol_increase = scenario.get("volatility_increase", 2.0)
        duration = scenario.get("duration_days", 60)

        portfolio_returns = (returns_df * weights).sum(axis=1)
        mean_return = portfolio_returns.mean()
        std_return = portfolio_returns.std()

        stressed_mean = mean_return + (market_drop / duration)
        stressed_std = std_return * vol_increase

        np.random.seed(42)
        stressed_returns = np.random.normal(stressed_mean, stressed_std, duration)

        cumulative_return = (1 + stressed_returns).prod() - 1
        loss = cumulative_return * 100

        return {
            "name": "Custom Scenario",
            "parameters": {
                "market_drop_percent": round(market_drop * 100, 2),
                "volatility_multiplier": vol_increase,
                "duration_days": duration
            },
            "expected_loss_percent": round(loss, 2),
            "stressed_volatility": round(stressed_std * np.sqrt(252) * 100, 2),
            "severity": self._assess_severity(loss)
        }

    def _worst_case_scenario(self, returns: pd.Series, simulations: int) -> Dict:
        """Monte Carlo worst case analysis"""
        mean_return = returns.mean()
        std_return = returns.std()

        # Extreme stress: 3x volatility, significant negative drift
        extreme_std = std_return * 3.0
        extreme_mean = mean_return - 2 * std_return

        # Run simulations
        np.random.seed(42)
        simulation_results = []

        for _ in range(simulations):
            scenario_returns = np.random.normal(extreme_mean, extreme_std, 60)  # 60 days
            cumulative = (1 + scenario_returns).prod() - 1
            simulation_results.append(cumulative)

        simulation_results = np.array(simulation_results)

        # Worst percentiles
        worst_1pct = np.percentile(simulation_results, 1) * 100
        worst_5pct = np.percentile(simulation_results, 5) * 100
        worst_10pct = np.percentile(simulation_results, 10) * 100

        return {
            "name": "Worst Case Monte Carlo",
            "simulations": simulations,
            "parameters": {
                "volatility_multiplier": 3.0,
                "negative_drift": "2 std dev"
            },
            "worst_1_percent": round(worst_1pct, 2),
            "worst_5_percent": round(worst_5pct, 2),
            "worst_10_percent": round(worst_10pct, 2),
            "severity": "EXTREME"
        }

    def _worst_case_scenario_portfolio(
        self, returns_df: pd.DataFrame, weights: np.ndarray, simulations: int
    ) -> Dict:
        """Portfolio worst case Monte Carlo"""
        portfolio_returns = (returns_df * weights).sum(axis=1)
        mean_return = portfolio_returns.mean()
        std_return = portfolio_returns.std()

        extreme_std = std_return * 3.0
        extreme_mean = mean_return - 2 * std_return

        np.random.seed(42)
        simulation_results = []

        for _ in range(simulations):
            scenario_returns = np.random.normal(extreme_mean, extreme_std, 60)
            cumulative = (1 + scenario_returns).prod() - 1
            simulation_results.append(cumulative)

        simulation_results = np.array(simulation_results)

        worst_1pct = np.percentile(simulation_results, 1) * 100
        worst_5pct = np.percentile(simulation_results, 5) * 100
        worst_10pct = np.percentile(simulation_results, 10) * 100

        return {
            "name": "Worst Case Monte Carlo",
            "simulations": simulations,
            "parameters": {
                "volatility_multiplier": 3.0,
                "negative_drift": "2 std dev"
            },
            "worst_1_percent": round(worst_1pct, 2),
            "worst_5_percent": round(worst_5pct, 2),
            "worst_10_percent": round(worst_10pct, 2),
            "severity": "EXTREME"
        }

    def _assess_severity(self, loss_percent: float) -> str:
        """Assess severity of loss"""
        loss = abs(loss_percent)
        if loss < 10:
            return "LOW"
        elif loss < 20:
            return "MODERATE"
        elif loss < 35:
            return "HIGH"
        elif loss < 50:
            return "SEVERE"
        else:
            return "CATASTROPHIC"

    def _generate_assessment(self, scenarios: Dict) -> Dict:
        """Generate overall stress test assessment"""
        if not scenarios:
            return {}

        # Find worst scenario
        worst_scenario = None
        worst_loss = 0

        for name, scenario in scenarios.items():
            loss = abs(scenario.get("expected_loss_percent", 0))
            if loss > worst_loss:
                worst_loss = loss
                worst_scenario = name

        # Count severity levels
        severity_counts = {"LOW": 0, "MODERATE": 0, "HIGH": 0, "SEVERE": 0, "CATASTROPHIC": 0, "EXTREME": 0}
        for scenario in scenarios.values():
            severity = scenario.get("severity", "UNKNOWN")
            if severity in severity_counts:
                severity_counts[severity] += 1

        # Generate recommendations
        recommendations = []
        if worst_loss > 50:
            recommendations.append("CRITICAL: Portfolio faces catastrophic risk in extreme scenarios. Consider significant hedging or risk reduction.")
        elif worst_loss > 35:
            recommendations.append("Severe risk exposure detected. Recommend defensive positioning and tail risk hedges.")
        elif worst_loss > 20:
            recommendations.append("High stress scenario risk. Consider diversification and volatility hedges.")
        elif worst_loss > 10:
            recommendations.append("Moderate stress risk. Monitor exposure and maintain adequate reserves.")
        else:
            recommendations.append("Resilient portfolio under stress scenarios tested.")

        if severity_counts["SEVERE"] + severity_counts["CATASTROPHIC"] >= 2:
            recommendations.append("Multiple severe scenarios detected. Review asset allocation and correlation structure.")

        return {
            "worst_scenario": worst_scenario,
            "worst_loss_percent": round(worst_loss, 2),
            "severity_distribution": severity_counts,
            "overall_resilience": self._assess_resilience(worst_loss),
            "recommendations": recommendations
        }

    def _assess_resilience(self, worst_loss: float) -> str:
        """Assess overall portfolio resilience"""
        if worst_loss < 15:
            return "EXCELLENT"
        elif worst_loss < 25:
            return "GOOD"
        elif worst_loss < 40:
            return "FAIR"
        elif worst_loss < 60:
            return "POOR"
        else:
            return "CRITICAL"
