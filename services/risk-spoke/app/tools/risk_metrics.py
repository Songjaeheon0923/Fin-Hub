"""
Risk Metrics Calculator Tool
Calculates Sharpe Ratio, Sortino Ratio, Maximum Drawdown, Beta, Alpha, and other risk metrics
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional
from scipy import stats
from datetime import datetime


class RiskMetricsTool:
    """Calculate comprehensive risk and performance metrics"""

    def __init__(self):
        self.data_dir = Path(__file__).parent.parent.parent.parent.parent / "data" / "stock-data"
        self.risk_free_rate = 0.04  # Default 4% annual risk-free rate (approximate 2025 Treasury rate)

    async def get_tool_info(self) -> Dict:
        """Get tool information for MCP protocol"""
        return {
            "name": "risk_calculate_metrics",
            "description": "Calculate risk and performance metrics: Sharpe, Sortino, Max Drawdown, Beta, Alpha, etc.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock symbol (e.g., AAPL, MSFT)"
                    },
                    "benchmark": {
                        "type": "string",
                        "description": "Benchmark symbol for Beta/Alpha (default: SPY)"
                    },
                    "period": {
                        "type": "integer",
                        "description": "Analysis period in days (default: 252 = 1 year)"
                    },
                    "risk_free_rate": {
                        "type": "number",
                        "description": "Annual risk-free rate (default: 0.04 = 4%)"
                    },
                    "metrics": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific metrics to calculate or ['all']"
                    }
                },
                "required": ["symbol"]
            }
        }

    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute risk metrics calculation"""
        try:
            symbol = arguments.get("symbol", "").upper()
            benchmark = arguments.get("benchmark", "SPY").upper()
            period = arguments.get("period", 252)
            rf_rate = arguments.get("risk_free_rate", self.risk_free_rate)
            metrics_list = arguments.get("metrics", ["all"])

            # Validation
            if not symbol:
                return {"error": "Symbol is required"}

            # Load stock data
            data_file = self.data_dir / f"{symbol}.csv"
            if not data_file.exists():
                return {"error": f"No data available for {symbol}"}

            df = pd.read_csv(data_file, index_col=0, parse_dates=True)

            if df.empty or 'Close' not in df.columns:
                return {"error": f"Invalid data for {symbol}"}

            # Get recent data
            df = df.tail(period)

            if len(df) < 30:
                return {"error": f"Insufficient data: only {len(df)} days available"}

            # Calculate returns
            returns = df['Close'].pct_change().dropna()

            # Initialize result
            result = {
                "symbol": symbol,
                "period_days": len(df),
                "start_date": df.index.min().isoformat(),
                "end_date": df.index.max().isoformat(),
                "risk_free_rate": rf_rate,
                "metrics": {}
            }

            # Calculate requested metrics
            calc_all = "all" in metrics_list

            if calc_all or "sharpe" in metrics_list:
                result["metrics"]["sharpe_ratio"] = self._calculate_sharpe(returns, rf_rate)

            if calc_all or "sortino" in metrics_list:
                result["metrics"]["sortino_ratio"] = self._calculate_sortino(returns, rf_rate)

            if calc_all or "drawdown" in metrics_list:
                result["metrics"]["max_drawdown"] = self._calculate_max_drawdown(df['Close'])

            if calc_all or "volatility" in metrics_list:
                result["metrics"]["volatility"] = self._calculate_volatility(returns)

            if calc_all or "returns" in metrics_list:
                result["metrics"]["returns"] = self._calculate_returns(df['Close'])

            if calc_all or "beta" in metrics_list or "alpha" in metrics_list:
                benchmark_data = self._load_benchmark(benchmark, period)
                if benchmark_data is not None:
                    beta_alpha = self._calculate_beta_alpha(
                        df['Close'], benchmark_data, rf_rate
                    )
                    # Check if calculation succeeded
                    if "error" not in beta_alpha:
                        if calc_all or "beta" in metrics_list:
                            result["metrics"]["beta"] = beta_alpha["beta"]
                        if calc_all or "alpha" in metrics_list:
                            result["metrics"]["alpha"] = beta_alpha["alpha"]
                        result["benchmark"] = benchmark
                    else:
                        result["warning"] = beta_alpha["error"]
                else:
                    if calc_all or "beta" in metrics_list or "alpha" in metrics_list:
                        result["warning"] = f"Benchmark {benchmark} data not available"

            if calc_all or "information_ratio" in metrics_list:
                if "benchmark" in result:
                    benchmark_data = self._load_benchmark(benchmark, period)
                    if benchmark_data is not None:
                        result["metrics"]["information_ratio"] = self._calculate_information_ratio(
                            returns, benchmark_data
                        )

            if calc_all or "calmar" in metrics_list:
                result["metrics"]["calmar_ratio"] = self._calculate_calmar(
                    df['Close'], rf_rate
                )

            if calc_all or "downside_deviation" in metrics_list:
                result["metrics"]["downside_deviation"] = self._calculate_downside_deviation(returns)

            # Add interpretation
            result["interpretation"] = self._generate_interpretation(result["metrics"])

            return result

        except Exception as e:
            return {"error": f"Risk metrics calculation failed: {str(e)}"}

    def _calculate_sharpe(self, returns: pd.Series, rf_rate: float) -> Dict:
        """Calculate Sharpe Ratio"""
        # Annualize returns
        annual_return = returns.mean() * 252
        annual_std = returns.std() * np.sqrt(252)

        # Calculate Sharpe ratio
        sharpe = (annual_return - rf_rate) / annual_std if annual_std > 0 else 0

        return {
            "value": round(sharpe, 4),
            "annual_return": round(annual_return * 100, 2),
            "annual_volatility": round(annual_std * 100, 2),
            "interpretation": self._interpret_sharpe(sharpe)
        }

    def _interpret_sharpe(self, sharpe: float) -> str:
        """Interpret Sharpe Ratio value"""
        if sharpe < 0:
            return "Negative - Investment underperforms risk-free rate"
        elif sharpe < 1:
            return "Below 1 - Sub-optimal risk-adjusted return"
        elif sharpe < 2:
            return "Good - Acceptable risk-adjusted return"
        elif sharpe < 3:
            return "Very Good - Strong risk-adjusted return"
        else:
            return "Excellent - Outstanding risk-adjusted return"

    def _calculate_sortino(self, returns: pd.Series, rf_rate: float) -> Dict:
        """Calculate Sortino Ratio (only penalizes downside volatility)"""
        annual_return = returns.mean() * 252

        # Calculate downside deviation (only negative returns)
        downside_returns = returns[returns < 0]
        downside_std = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else returns.std() * np.sqrt(252)

        # Calculate Sortino ratio
        sortino = (annual_return - rf_rate) / downside_std if downside_std > 0 else 0

        return {
            "value": round(sortino, 4),
            "downside_deviation": round(downside_std * 100, 2),
            "interpretation": "Better than Sharpe" if sortino > 0 else "Focuses on downside risk only"
        }

    def _calculate_max_drawdown(self, prices: pd.Series) -> Dict:
        """Calculate Maximum Drawdown"""
        # Calculate cumulative returns
        cumulative = (1 + prices.pct_change()).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max

        max_dd = drawdown.min()
        max_dd_idx = drawdown.idxmin()

        # Find peak before drawdown
        peak_idx = cumulative[:max_dd_idx].idxmax()

        # Calculate recovery
        recovery_idx = None
        # Get position in index instead of comparing timestamps
        max_dd_pos = cumulative.index.get_loc(max_dd_idx)
        if max_dd_pos < len(cumulative) - 1:
            post_dd = cumulative[max_dd_idx:]
            peak_value = cumulative[peak_idx]
            recovery = post_dd[post_dd >= peak_value]
            if len(recovery) > 0:
                recovery_idx = recovery.index[0]

        # Calculate duration safely
        try:
            duration = (max_dd_idx - peak_idx).days
        except:
            # If dates are not comparable, estimate from index positions
            peak_pos = prices.index.get_loc(peak_idx) if hasattr(prices.index, 'get_loc') else 0
            trough_pos = prices.index.get_loc(max_dd_idx) if hasattr(prices.index, 'get_loc') else 0
            duration = trough_pos - peak_pos

        return {
            "max_drawdown_percent": round(max_dd * 100, 2),
            "peak_date": peak_idx.isoformat() if hasattr(peak_idx, 'isoformat') else str(peak_idx),
            "trough_date": max_dd_idx.isoformat() if hasattr(max_dd_idx, 'isoformat') else str(max_dd_idx),
            "recovery_date": recovery_idx.isoformat() if recovery_idx and hasattr(recovery_idx, 'isoformat') else ("Not recovered" if not recovery_idx else str(recovery_idx)),
            "drawdown_duration_days": duration,
            "interpretation": self._interpret_drawdown(max_dd)
        }

    def _interpret_drawdown(self, max_dd: float) -> str:
        """Interpret Maximum Drawdown"""
        dd_pct = abs(max_dd * 100)
        if dd_pct < 10:
            return "Low risk - Small maximum loss"
        elif dd_pct < 20:
            return "Moderate risk - Acceptable drawdown"
        elif dd_pct < 30:
            return "High risk - Significant drawdown"
        else:
            return "Very high risk - Severe drawdown"

    def _calculate_volatility(self, returns: pd.Series) -> Dict:
        """Calculate volatility metrics"""
        daily_vol = returns.std()
        annual_vol = daily_vol * np.sqrt(252)

        return {
            "daily_percent": round(daily_vol * 100, 4),
            "annual_percent": round(annual_vol * 100, 2),
            "interpretation": self._interpret_volatility(annual_vol)
        }

    def _interpret_volatility(self, annual_vol: float) -> str:
        """Interpret volatility level"""
        vol_pct = annual_vol * 100
        if vol_pct < 15:
            return "Low volatility - Stable asset"
        elif vol_pct < 25:
            return "Moderate volatility - Normal for stocks"
        elif vol_pct < 40:
            return "High volatility - Risky asset"
        else:
            return "Very high volatility - Extremely risky"

    def _calculate_returns(self, prices: pd.Series) -> Dict:
        """Calculate return metrics"""
        total_return = (prices.iloc[-1] - prices.iloc[0]) / prices.iloc[0]

        # Annualized return
        days = len(prices)
        years = days / 252
        annual_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0

        # Calculate returns for different periods
        returns_data = {
            "total_percent": round(total_return * 100, 2),
            "annualized_percent": round(annual_return * 100, 2),
            "start_price": round(prices.iloc[0], 2),
            "end_price": round(prices.iloc[-1], 2)
        }

        # Add period-specific returns if enough data
        if len(prices) >= 252:
            returns_data["1y_return"] = round(((prices.iloc[-1] / prices.iloc[-252]) - 1) * 100, 2)
        if len(prices) >= 126:
            returns_data["6m_return"] = round(((prices.iloc[-1] / prices.iloc[-126]) - 1) * 100, 2)
        if len(prices) >= 63:
            returns_data["3m_return"] = round(((prices.iloc[-1] / prices.iloc[-63]) - 1) * 100, 2)
        if len(prices) >= 21:
            returns_data["1m_return"] = round(((prices.iloc[-1] / prices.iloc[-21]) - 1) * 100, 2)

        return returns_data

    def _load_benchmark(self, benchmark: str, period: int) -> Optional[pd.Series]:
        """Load benchmark data"""
        try:
            benchmark_file = self.data_dir / f"{benchmark}.csv"
            if not benchmark_file.exists():
                return None

            df = pd.read_csv(benchmark_file, index_col=0, parse_dates=True)
            if df.empty or 'Close' not in df.columns:
                return None

            return df['Close'].tail(period)
        except:
            return None

    def _calculate_beta_alpha(
        self, prices: pd.Series, benchmark_prices: pd.Series, rf_rate: float
    ) -> Dict:
        """Calculate Beta and Alpha (CAPM)"""
        # Align data
        aligned = pd.concat([prices, benchmark_prices], axis=1, keys=['stock', 'benchmark']).dropna()

        if len(aligned) < 30:
            return {"error": "Insufficient overlapping data"}

        # Calculate returns
        stock_returns = aligned['stock'].pct_change().dropna()
        benchmark_returns = aligned['benchmark'].pct_change().dropna()

        # Calculate beta using covariance
        covariance = np.cov(stock_returns, benchmark_returns)[0][1]
        benchmark_variance = np.var(benchmark_returns)
        beta = covariance / benchmark_variance if benchmark_variance > 0 else 1

        # Calculate alpha
        stock_annual_return = stock_returns.mean() * 252
        benchmark_annual_return = benchmark_returns.mean() * 252
        alpha = stock_annual_return - (rf_rate + beta * (benchmark_annual_return - rf_rate))

        # R-squared
        correlation = np.corrcoef(stock_returns, benchmark_returns)[0][1]
        r_squared = correlation ** 2

        return {
            "beta": {
                "value": round(beta, 4),
                "r_squared": round(r_squared, 4),
                "interpretation": self._interpret_beta(beta)
            },
            "alpha": {
                "annual_percent": round(alpha * 100, 2),
                "interpretation": self._interpret_alpha(alpha)
            }
        }

    def _interpret_beta(self, beta: float) -> str:
        """Interpret Beta value"""
        if beta < 0:
            return "Negative correlation with market"
        elif beta < 0.5:
            return "Low volatility - Less risky than market"
        elif beta < 1:
            return "Below market volatility"
        elif beta == 1:
            return "Moves with the market"
        elif beta < 1.5:
            return "Above market volatility"
        else:
            return "High volatility - Much riskier than market"

    def _interpret_alpha(self, alpha: float) -> str:
        """Interpret Alpha value"""
        alpha_pct = alpha * 100
        if alpha_pct > 2:
            return "Significant outperformance vs. expected return"
        elif alpha_pct > 0:
            return "Modest outperformance"
        elif alpha_pct > -2:
            return "Slight underperformance"
        else:
            return "Significant underperformance"

    def _calculate_information_ratio(
        self, returns: pd.Series, benchmark_prices: pd.Series
    ) -> Dict:
        """Calculate Information Ratio (IR)"""
        benchmark_returns = benchmark_prices.pct_change().dropna()

        # Align returns
        aligned = pd.concat([returns, benchmark_returns], axis=1, keys=['stock', 'benchmark']).dropna()

        if len(aligned) < 2:
            return {"error": "Insufficient data"}

        # Calculate excess returns
        excess_returns = aligned['stock'] - aligned['benchmark']

        # Information ratio
        ir = (excess_returns.mean() * 252) / (excess_returns.std() * np.sqrt(252)) if excess_returns.std() > 0 else 0

        return {
            "value": round(ir, 4),
            "interpretation": "Measures consistency of outperformance vs. benchmark"
        }

    def _calculate_calmar(self, prices: pd.Series, rf_rate: float) -> Dict:
        """Calculate Calmar Ratio (return / max drawdown)"""
        total_return = (prices.iloc[-1] - prices.iloc[0]) / prices.iloc[0]
        days = len(prices)
        years = days / 252
        annual_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0

        max_dd_dict = self._calculate_max_drawdown(prices)
        max_dd = abs(max_dd_dict["max_drawdown_percent"]) / 100

        calmar = annual_return / max_dd if max_dd > 0 else 0

        return {
            "value": round(calmar, 4),
            "interpretation": "Higher is better - measures return per unit of drawdown risk"
        }

    def _calculate_downside_deviation(self, returns: pd.Series) -> Dict:
        """Calculate downside deviation"""
        negative_returns = returns[returns < 0]
        downside_dev = negative_returns.std() * np.sqrt(252) if len(negative_returns) > 0 else 0

        return {
            "annual_percent": round(downside_dev * 100, 2),
            "negative_days": len(negative_returns),
            "negative_days_percent": round((len(negative_returns) / len(returns)) * 100, 2)
        }

    def _generate_interpretation(self, metrics: Dict) -> Dict:
        """Generate overall interpretation"""
        interpretation = {
            "risk_level": "Unknown",
            "return_quality": "Unknown",
            "recommendation": []
        }

        # Assess risk level
        if "volatility" in metrics:
            vol = metrics["volatility"]["annual_percent"]
            if vol < 15:
                interpretation["risk_level"] = "Low"
            elif vol < 25:
                interpretation["risk_level"] = "Moderate"
            elif vol < 40:
                interpretation["risk_level"] = "High"
            else:
                interpretation["risk_level"] = "Very High"

        # Assess return quality
        if "sharpe_ratio" in metrics:
            sharpe = metrics["sharpe_ratio"]["value"]
            if sharpe > 2:
                interpretation["return_quality"] = "Excellent"
            elif sharpe > 1:
                interpretation["return_quality"] = "Good"
            elif sharpe > 0:
                interpretation["return_quality"] = "Fair"
            else:
                interpretation["return_quality"] = "Poor"

        # Generate recommendations
        if "sharpe_ratio" in metrics and metrics["sharpe_ratio"]["value"] < 1:
            interpretation["recommendation"].append("Consider alternative investments with better risk-adjusted returns")

        if "max_drawdown" in metrics and abs(metrics["max_drawdown"]["max_drawdown_percent"]) > 30:
            interpretation["recommendation"].append("High drawdown risk - consider position sizing or hedging")

        if "beta" in metrics:
            beta_val = metrics["beta"]["value"]
            if beta_val > 1.5:
                interpretation["recommendation"].append("High market sensitivity - diversification recommended")

        if not interpretation["recommendation"]:
            interpretation["recommendation"].append("Risk profile appears acceptable for the asset class")

        return interpretation
