"""
Stock Comparison Tool - Compare multiple stocks for correlation and performance analysis
Analyzes relative performance, correlation, and comparative metrics
"""

import sys
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
from pathlib import Path


class StockComparisonTool:
    """Compare multiple stocks for correlation and performance analysis"""

    def __init__(self):
        self.data_dir = Path(__file__).parent.parent.parent.parent.parent / 'data' / 'stock-data'

    async def get_tool_info(self) -> Dict:
        """Get tool information for MCP protocol"""
        return {
            "name": "market.stock_comparison",
            "description": "Compare multiple stocks for correlation, performance, and relative analysis",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "symbols": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of stock symbols to compare (2-10 stocks)",
                        "minItems": 2,
                        "maxItems": 10
                    },
                    "period": {
                        "type": "integer",
                        "description": "Number of days for analysis (default: 90)",
                        "default": 90
                    },
                    "metrics": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["correlation", "performance", "volatility", "risk_return", "all"]
                        },
                        "description": "Metrics to compare (default: all)",
                        "default": ["all"]
                    }
                },
                "required": ["symbols"]
            }
        }

    def _load_stock_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """Load stock data from CSV file"""
        try:
            file_path = self.data_dir / f"{symbol.upper()}.csv"
            if not file_path.exists():
                return None

            df = pd.read_csv(file_path)
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.sort_values('Date')
            return df
        except Exception as e:
            print(f"Error loading data for {symbol}: {e}", file=sys.stderr)
            return None

    def _calculate_correlation(self, price_data: Dict[str, pd.Series]) -> Dict:
        """Calculate correlation matrix between stocks"""
        if len(price_data) < 2:
            return {}

        # Create DataFrame with all stock returns
        returns_df = pd.DataFrame()
        for symbol, prices in price_data.items():
            returns_df[symbol] = prices.pct_change()

        # Calculate correlation matrix
        corr_matrix = returns_df.corr()

        # Convert to dict format
        correlation_pairs = []
        symbols = list(price_data.keys())

        for i, sym1 in enumerate(symbols):
            for sym2 in symbols[i+1:]:
                corr_value = corr_matrix.loc[sym1, sym2]
                correlation_pairs.append({
                    "stock_1": sym1,
                    "stock_2": sym2,
                    "correlation": float(corr_value),
                    "relationship": self._interpret_correlation(corr_value)
                })

        # Sort by absolute correlation value
        correlation_pairs = sorted(correlation_pairs, key=lambda x: abs(x['correlation']), reverse=True)

        return {
            "correlation_matrix": corr_matrix.to_dict(),
            "top_correlations": correlation_pairs[:10]
        }

    def _interpret_correlation(self, corr: float) -> str:
        """Interpret correlation coefficient"""
        abs_corr = abs(corr)
        if abs_corr > 0.8:
            strength = "Very Strong"
        elif abs_corr > 0.6:
            strength = "Strong"
        elif abs_corr > 0.4:
            strength = "Moderate"
        elif abs_corr > 0.2:
            strength = "Weak"
        else:
            strength = "Very Weak"

        direction = "Positive" if corr > 0 else "Negative"
        return f"{strength} {direction}"

    def _calculate_performance(self, price_data: Dict[str, pd.Series], period: int) -> Dict:
        """Calculate performance metrics for each stock"""
        performance = {}

        for symbol, prices in price_data.items():
            if len(prices) < 2:
                continue

            start_price = prices.iloc[0]
            end_price = prices.iloc[-1]
            total_return = ((end_price - start_price) / start_price) * 100

            # Calculate annualized return
            days = len(prices)
            years = days / 252  # Trading days per year
            annualized_return = ((end_price / start_price) ** (1 / years) - 1) * 100 if years > 0 else 0

            # Calculate max/min during period
            max_price = prices.max()
            min_price = prices.min()
            max_return = ((max_price - start_price) / start_price) * 100
            max_drawdown = ((min_price - max_price) / max_price) * 100

            performance[symbol] = {
                "start_price": float(start_price),
                "end_price": float(end_price),
                "total_return_pct": float(total_return),
                "annualized_return_pct": float(annualized_return),
                "max_price": float(max_price),
                "min_price": float(min_price),
                "max_gain_pct": float(max_return),
                "max_drawdown_pct": float(max_drawdown),
                "period_days": days
            }

        # Rank by total return
        ranked = sorted(performance.items(), key=lambda x: x[1]['total_return_pct'], reverse=True)

        return {
            "individual_performance": performance,
            "ranking": [{"symbol": sym, "return_pct": perf['total_return_pct']} for sym, perf in ranked]
        }

    def _calculate_volatility(self, price_data: Dict[str, pd.Series]) -> Dict:
        """Calculate volatility metrics for each stock"""
        volatility = {}

        for symbol, prices in price_data.items():
            returns = prices.pct_change().dropna()

            # Annualized volatility
            daily_vol = returns.std()
            annual_vol = daily_vol * np.sqrt(252) * 100

            # Average absolute daily change
            avg_daily_change = abs(returns).mean() * 100

            volatility[symbol] = {
                "annualized_volatility_pct": float(annual_vol),
                "avg_daily_change_pct": float(avg_daily_change),
                "risk_level": self._interpret_volatility(annual_vol)
            }

        # Rank by volatility
        ranked = sorted(volatility.items(), key=lambda x: x[1]['annualized_volatility_pct'], reverse=True)

        return {
            "individual_volatility": volatility,
            "ranking": [{"symbol": sym, "volatility_pct": vol['annualized_volatility_pct']} for sym, vol in ranked]
        }

    def _interpret_volatility(self, annual_vol: float) -> str:
        """Interpret volatility level"""
        if annual_vol < 15:
            return "Low Risk"
        elif annual_vol < 25:
            return "Moderate Risk"
        elif annual_vol < 40:
            return "High Risk"
        else:
            return "Very High Risk"

    def _calculate_risk_return(self, price_data: Dict[str, pd.Series]) -> Dict:
        """Calculate risk-adjusted return metrics (Sharpe-like ratio)"""
        risk_return = {}

        for symbol, prices in price_data.items():
            returns = prices.pct_change().dropna()

            if len(returns) < 2:
                continue

            # Calculate average return
            avg_return = returns.mean() * 252 * 100  # Annualized

            # Calculate volatility
            volatility = returns.std() * np.sqrt(252) * 100

            # Simple risk-adjusted return (return / volatility)
            if volatility > 0:
                risk_adjusted_return = avg_return / volatility
            else:
                risk_adjusted_return = 0

            risk_return[symbol] = {
                "avg_annual_return_pct": float(avg_return),
                "annual_volatility_pct": float(volatility),
                "risk_adjusted_return": float(risk_adjusted_return),
                "rating": self._rate_risk_return(risk_adjusted_return)
            }

        # Rank by risk-adjusted return
        ranked = sorted(risk_return.items(), key=lambda x: x[1]['risk_adjusted_return'], reverse=True)

        return {
            "individual_metrics": risk_return,
            "ranking": [{"symbol": sym, "score": rr['risk_adjusted_return']} for sym, rr in ranked]
        }

    def _rate_risk_return(self, ratio: float) -> str:
        """Rate risk-adjusted return"""
        if ratio > 1.5:
            return "Excellent"
        elif ratio > 1.0:
            return "Good"
        elif ratio > 0.5:
            return "Fair"
        else:
            return "Poor"

    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute stock comparison analysis"""
        symbols = arguments.get("symbols", [])
        period = arguments.get("period", 90)
        requested_metrics = arguments.get("metrics", ["all"])

        if not symbols or len(symbols) < 2:
            return {"error": "At least 2 symbols are required for comparison"}

        if len(symbols) > 10:
            return {"error": "Maximum 10 symbols allowed for comparison"}

        # Load data for all symbols
        price_data = {}
        failed_symbols = []

        for symbol in symbols:
            df = self._load_stock_data(symbol.upper())
            if df is None:
                failed_symbols.append(symbol.upper())
                continue

            # Get recent data
            df_recent = df.tail(period + 50)
            if len(df_recent) >= period:
                price_data[symbol.upper()] = df_recent['Close'].tail(period)
            else:
                failed_symbols.append(symbol.upper())

        if len(price_data) < 2:
            return {
                "error": "Insufficient data for comparison",
                "failed_symbols": failed_symbols,
                "available_symbols": list(price_data.keys())
            }

        # Determine which metrics to calculate
        calc_all = "all" in requested_metrics
        results = {
            "symbols_analyzed": list(price_data.keys()),
            "failed_symbols": failed_symbols,
            "period_days": period
        }

        # Calculate correlation
        if calc_all or "correlation" in requested_metrics:
            results["correlation"] = self._calculate_correlation(price_data)

        # Calculate performance
        if calc_all or "performance" in requested_metrics:
            results["performance"] = self._calculate_performance(price_data, period)

        # Calculate volatility
        if calc_all or "volatility" in requested_metrics:
            results["volatility"] = self._calculate_volatility(price_data)

        # Calculate risk-return
        if calc_all or "risk_return" in requested_metrics:
            results["risk_return"] = self._calculate_risk_return(price_data)

        # Generate summary
        results["summary"] = self._generate_summary(results)
        results["data_source"] = "Historical CSV data"

        return results

    def _generate_summary(self, results: Dict) -> str:
        """Generate human-readable summary"""
        summary_parts = []

        symbols = results.get("symbols_analyzed", [])
        summary_parts.append(f"Comparing {len(symbols)} stocks: {', '.join(symbols)}")

        # Best performer
        if "performance" in results and "ranking" in results["performance"]:
            ranking = results["performance"]["ranking"]
            if ranking:
                best = ranking[0]
                summary_parts.append(f"Best performer: {best['symbol']} ({best['return_pct']:.2f}%)")

        # Highest correlation
        if "correlation" in results and "top_correlations" in results["correlation"]:
            top_corr = results["correlation"]["top_correlations"]
            if top_corr:
                corr = top_corr[0]
                summary_parts.append(
                    f"Highest correlation: {corr['stock_1']}-{corr['stock_2']} ({corr['correlation']:.2f})"
                )

        # Best risk-adjusted
        if "risk_return" in results and "ranking" in results["risk_return"]:
            ranking = results["risk_return"]["ranking"]
            if ranking:
                best = ranking[0]
                summary_parts.append(f"Best risk-adjusted: {best['symbol']} ({best['score']:.2f})")

        return " | ".join(summary_parts) if summary_parts else "Comparison completed"


# Export for MCP server
__all__ = ['StockComparisonTool']
