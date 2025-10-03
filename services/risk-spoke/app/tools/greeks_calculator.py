"""
Greeks Calculator Tool
Calculates option Greeks using Black-Scholes model
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional
from scipy import stats
from datetime import datetime, timedelta


class GreeksCalculatorTool:
    """Calculate option Greeks using Black-Scholes-Merton model"""

    def __init__(self):
        self.data_dir = Path(__file__).parent.parent.parent.parent.parent / "data" / "stock-data"

    async def get_tool_info(self) -> Dict:
        """Get tool information for MCP protocol"""
        return {
            "name": "risk.calculate_greeks",
            "description": "Calculate option Greeks (Delta, Gamma, Vega, Theta, Rho) using Black-Scholes model",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock symbol (e.g., AAPL, TSLA)"
                    },
                    "option_type": {
                        "type": "string",
                        "enum": ["call", "put", "both"],
                        "description": "Option type (default: both)"
                    },
                    "strike_price": {
                        "type": "number",
                        "description": "Strike price (default: current price - ATM)"
                    },
                    "time_to_expiry": {
                        "type": "number",
                        "description": "Time to expiration in days (default: 30)"
                    },
                    "risk_free_rate": {
                        "type": "number",
                        "description": "Risk-free interest rate (default: 0.04)"
                    },
                    "volatility": {
                        "type": "number",
                        "description": "Implied volatility (default: use historical volatility)"
                    },
                    "dividend_yield": {
                        "type": "number",
                        "description": "Annual dividend yield (default: 0)"
                    },
                    "greeks": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Greeks to calculate: delta, gamma, vega, theta, rho, all"
                    }
                },
                "required": ["symbol"]
            }
        }

    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Greeks calculation"""
        try:
            symbol = arguments.get("symbol", "").upper()
            option_type = arguments.get("option_type", "both").lower()
            strike_price = arguments.get("strike_price")
            tte_days = arguments.get("time_to_expiry", 30)
            risk_free_rate = arguments.get("risk_free_rate", 0.04)
            custom_vol = arguments.get("volatility")
            dividend_yield = arguments.get("dividend_yield", 0)
            greeks_to_calc = arguments.get("greeks", ["all"])

            # Validation
            if not symbol:
                return {"error": "Symbol is required"}

            if option_type not in ["call", "put", "both"]:
                return {"error": "Option type must be 'call', 'put', or 'both'"}

            # Load data
            data_file = self.data_dir / f"{symbol}.csv"
            if not data_file.exists():
                return {"error": f"No data available for {symbol}"}

            df = pd.read_csv(data_file, index_col=0, parse_dates=True)
            if df.empty or 'Close' not in df.columns:
                return {"error": f"Invalid data for {symbol}"}

            # Get current price
            current_price = df['Close'].iloc[-1]

            # Default strike to ATM
            if strike_price is None:
                strike_price = current_price

            # Calculate historical volatility if not provided
            if custom_vol is None:
                returns = df['Close'].pct_change().tail(252).dropna()
                volatility = returns.std() * np.sqrt(252)
            else:
                volatility = custom_vol

            # Time to expiry in years
            T = tte_days / 365.0

            if T <= 0:
                return {"error": "Time to expiry must be positive"}

            # Determine which Greeks to calculate
            if "all" in greeks_to_calc:
                greeks_to_calc = ["delta", "gamma", "vega", "theta", "rho"]

            result = {
                "symbol": symbol,
                "spot_price": round(current_price, 2),
                "strike_price": round(strike_price, 2),
                "moneyness": round((current_price / strike_price - 1) * 100, 2),
                "time_to_expiry_days": tte_days,
                "time_to_expiry_years": round(T, 4),
                "volatility_annual": round(volatility * 100, 2),
                "risk_free_rate": round(risk_free_rate * 100, 2),
                "dividend_yield": round(dividend_yield * 100, 2)
            }

            # Calculate Greeks for call and/or put
            if option_type in ["call", "both"]:
                call_greeks = self._calculate_greeks(
                    S=current_price,
                    K=strike_price,
                    T=T,
                    r=risk_free_rate,
                    sigma=volatility,
                    q=dividend_yield,
                    option_type="call",
                    greeks_list=greeks_to_calc
                )
                result["call"] = call_greeks

            if option_type in ["put", "both"]:
                put_greeks = self._calculate_greeks(
                    S=current_price,
                    K=strike_price,
                    T=T,
                    r=risk_free_rate,
                    sigma=volatility,
                    q=dividend_yield,
                    option_type="put",
                    greeks_list=greeks_to_calc
                )
                result["put"] = put_greeks

            # Add interpretation
            result["interpretation"] = self._generate_interpretation(
                result, option_type, current_price, strike_price
            )

            return result

        except Exception as e:
            return {"error": f"Greeks calculation failed: {str(e)}"}

    def _calculate_greeks(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        q: float,
        option_type: str,
        greeks_list: list
    ) -> Dict:
        """Calculate option Greeks using Black-Scholes-Merton model"""

        # Black-Scholes d1 and d2
        d1 = (np.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)

        # Standard normal CDF and PDF
        N_d1 = stats.norm.cdf(d1)
        N_d2 = stats.norm.cdf(d2)
        n_d1 = stats.norm.pdf(d1)  # PDF for gamma, vega

        # For put options
        N_minus_d1 = stats.norm.cdf(-d1)
        N_minus_d2 = stats.norm.cdf(-d2)

        greeks = {}

        # Option price (for reference)
        if option_type == "call":
            price = S * np.exp(-q * T) * N_d1 - K * np.exp(-r * T) * N_d2
        else:  # put
            price = K * np.exp(-r * T) * N_minus_d2 - S * np.exp(-q * T) * N_minus_d1

        greeks["price"] = round(price, 4)
        greeks["intrinsic_value"] = round(max(0, (S - K) if option_type == "call" else (K - S)), 4)
        greeks["time_value"] = round(price - greeks["intrinsic_value"], 4)

        # Delta: ∂V/∂S
        if "delta" in greeks_list:
            if option_type == "call":
                delta = np.exp(-q * T) * N_d1
            else:  # put
                delta = -np.exp(-q * T) * N_minus_d1

            greeks["delta"] = {
                "value": round(delta, 4),
                "interpretation": self._interpret_delta(delta, option_type),
                "hedge_ratio": round(delta * 100, 2)  # per 100 shares
            }

        # Gamma: ∂²V/∂S² (same for call and put)
        if "gamma" in greeks_list:
            gamma = np.exp(-q * T) * n_d1 / (S * sigma * np.sqrt(T))

            greeks["gamma"] = {
                "value": round(gamma, 6),
                "interpretation": self._interpret_gamma(gamma),
                "gamma_dollars": round(gamma * S * S / 100, 4)  # Dollar gamma per 1% move
            }

        # Vega: ∂V/∂σ (same for call and put)
        if "vega" in greeks_list:
            vega = S * np.exp(-q * T) * n_d1 * np.sqrt(T) / 100  # Per 1% change in vol

            greeks["vega"] = {
                "value": round(vega, 4),
                "interpretation": self._interpret_vega(vega),
                "vega_percent": round(vega / price * 100, 2) if price > 0 else 0
            }

        # Theta: ∂V/∂T (time decay)
        if "theta" in greeks_list:
            if option_type == "call":
                theta = (
                    -(S * np.exp(-q * T) * n_d1 * sigma) / (2 * np.sqrt(T))
                    - r * K * np.exp(-r * T) * N_d2
                    + q * S * np.exp(-q * T) * N_d1
                ) / 365  # Per day
            else:  # put
                theta = (
                    -(S * np.exp(-q * T) * n_d1 * sigma) / (2 * np.sqrt(T))
                    + r * K * np.exp(-r * T) * N_minus_d2
                    - q * S * np.exp(-q * T) * N_minus_d1
                ) / 365  # Per day

            greeks["theta"] = {
                "value": round(theta, 4),
                "interpretation": self._interpret_theta(theta, option_type),
                "theta_percent": round(theta / price * 100, 2) if price > 0 else 0,
                "weekly_decay": round(theta * 7, 4)
            }

        # Rho: ∂V/∂r (interest rate sensitivity)
        if "rho" in greeks_list:
            if option_type == "call":
                rho = K * T * np.exp(-r * T) * N_d2 / 100  # Per 1% change in r
            else:  # put
                rho = -K * T * np.exp(-r * T) * N_minus_d2 / 100  # Per 1% change in r

            greeks["rho"] = {
                "value": round(rho, 4),
                "interpretation": self._interpret_rho(rho, option_type),
                "rho_percent": round(rho / price * 100, 2) if price > 0 else 0
            }

        return greeks

    def _interpret_delta(self, delta: float, option_type: str) -> str:
        """Interpret delta value"""
        abs_delta = abs(delta)

        if abs_delta < 0.25:
            moneyness = "Deep OTM" if option_type == "call" else "Deep ITM"
            direction = "Low probability of expiring ITM" if abs_delta < 0.25 else ""
        elif abs_delta < 0.45:
            moneyness = "OTM"
            direction = "Below 50% probability of expiring ITM"
        elif abs_delta < 0.55:
            moneyness = "ATM"
            direction = "Near 50% probability of expiring ITM"
        elif abs_delta < 0.75:
            moneyness = "ITM"
            direction = "Above 50% probability of expiring ITM"
        else:
            moneyness = "Deep ITM" if option_type == "call" else "Deep OTM"
            direction = "High probability of expiring ITM"

        sensitivity = f"{'Gains' if delta > 0 else 'Loses'} ${abs(delta):.2f} per $1 move in underlying"

        return f"{moneyness}. {direction}. {sensitivity}"

    def _interpret_gamma(self, gamma: float) -> str:
        """Interpret gamma value"""
        if gamma < 0.01:
            return "Low gamma - delta changes slowly with price moves"
        elif gamma < 0.05:
            return "Moderate gamma - delta moderately sensitive to price changes"
        elif gamma < 0.1:
            return "High gamma - delta very sensitive to price moves (ATM options)"
        else:
            return "Extremely high gamma - delta highly unstable, requires frequent rehedging"

    def _interpret_vega(self, vega: float) -> str:
        """Interpret vega value"""
        if vega < 0.05:
            return "Low vega - minimal sensitivity to volatility changes"
        elif vega < 0.15:
            return "Moderate vega - some sensitivity to vol changes"
        elif vega < 0.30:
            return "High vega - significant exposure to volatility"
        else:
            return "Very high vega - heavily exposed to implied volatility changes"

    def _interpret_theta(self, theta: float, option_type: str) -> str:
        """Interpret theta value"""
        abs_theta = abs(theta)

        if abs_theta < 0.01:
            decay = "Minimal time decay"
        elif abs_theta < 0.05:
            decay = "Moderate time decay"
        elif abs_theta < 0.10:
            decay = "Significant time decay"
        else:
            decay = "Severe time decay"

        direction = "Loses" if theta < 0 else "Gains"

        return f"{decay}. {direction} ${abs_theta:.4f} per day due to time decay"

    def _interpret_rho(self, rho: float, option_type: str) -> str:
        """Interpret rho value"""
        abs_rho = abs(rho)
        direction = "increases" if rho > 0 else "decreases"

        if abs_rho < 0.05:
            sensitivity = "Minimal"
        elif abs_rho < 0.15:
            sensitivity = "Low"
        elif abs_rho < 0.30:
            sensitivity = "Moderate"
        else:
            sensitivity = "High"

        return f"{sensitivity} interest rate sensitivity. Option value {direction} ${abs_rho:.4f} per 1% rate increase"

    def _generate_interpretation(
        self, result: Dict, option_type: str, spot: float, strike: float
    ) -> Dict:
        """Generate comprehensive interpretation"""
        moneyness_pct = result["moneyness"]

        # Determine moneyness category
        if abs(moneyness_pct) < 2:
            moneyness_desc = "At-the-money (ATM)"
            strategy_note = "Maximum gamma and vega exposure. High theta decay. Ideal for delta hedging and volatility trading."
        elif moneyness_pct > 10:
            moneyness_desc = "In-the-money (ITM)"
            strategy_note = "High delta, low gamma. Behaves more like the underlying stock. Lower time value."
        elif moneyness_pct < -10:
            moneyness_desc = "Out-of-the-money (OTM)"
            strategy_note = "Low delta, moderate gamma. High leverage but lower probability of profit. Primarily time value."
        else:
            moneyness_desc = "Near-the-money"
            strategy_note = "Balanced delta and gamma. Good for directional trades with volatility exposure."

        # Risk assessment
        vol_pct = result["volatility_annual"]
        tte_days = result["time_to_expiry_days"]

        if vol_pct > 60:
            vol_env = "High volatility environment - vega positive, consider selling premium"
        elif vol_pct > 35:
            vol_env = "Elevated volatility - mixed strategies advisable"
        elif vol_pct > 20:
            vol_env = "Normal volatility - standard option strategies applicable"
        else:
            vol_env = "Low volatility - consider buying options for protection"

        if tte_days < 7:
            time_env = "Very short dated - extreme theta decay, high gamma risk"
        elif tte_days < 30:
            time_env = "Short dated - accelerating theta decay, gamma exposure significant"
        elif tte_days < 90:
            time_env = "Medium term - balanced theta and gamma"
        else:
            time_env = "Long dated - low theta decay, vega dominant"

        recommendations = []

        # Add recommendations based on Greeks
        if option_type in ["call", "both"] and "call" in result:
            call = result["call"]
            if "delta" in call and abs(call["delta"]["value"]) > 0.7:
                recommendations.append("Call delta >0.7: Consider reducing size or hedging with short stock")
            if "gamma" in call and call["gamma"]["value"] > 0.1:
                recommendations.append("High gamma: Frequent rehedging needed for delta-neutral strategies")
            if "theta" in call and abs(call["theta"]["value"]) > 0.1:
                recommendations.append("High theta decay: Consider rolling to later expiry if holding long")

        if option_type in ["put", "both"] and "put" in result:
            put = result["put"]
            if "delta" in put and abs(put["delta"]["value"]) > 0.7:
                recommendations.append("Put delta <-0.7: Deep ITM, consider intrinsic value vs time value")
            if "vega" in put and put["vega"]["value"] > 0.3:
                recommendations.append("High vega: Significant exposure to volatility changes")

        if not recommendations:
            recommendations.append("Greeks within normal ranges for this configuration")

        return {
            "moneyness": moneyness_desc,
            "strategy_implications": strategy_note,
            "volatility_environment": vol_env,
            "time_environment": time_env,
            "recommendations": recommendations,
            "risk_factors": self._assess_risk_factors(result, option_type)
        }

    def _assess_risk_factors(self, result: Dict, option_type: str) -> Dict:
        """Assess primary risk factors"""
        risks = {
            "directional_risk": "MEDIUM",
            "volatility_risk": "MEDIUM",
            "time_decay_risk": "MEDIUM",
            "interest_rate_risk": "LOW"
        }

        # Assess directional risk (delta)
        max_delta = 0
        if option_type in ["call", "both"] and "call" in result and "delta" in result["call"]:
            max_delta = max(max_delta, abs(result["call"]["delta"]["value"]))
        if option_type in ["put", "both"] and "put" in result and "delta" in result["put"]:
            max_delta = max(max_delta, abs(result["put"]["delta"]["value"]))

        if max_delta > 0.7:
            risks["directional_risk"] = "HIGH"
        elif max_delta < 0.3:
            risks["directional_risk"] = "LOW"

        # Assess volatility risk (vega)
        max_vega = 0
        if option_type in ["call", "both"] and "call" in result and "vega" in result["call"]:
            max_vega = max(max_vega, abs(result["call"]["vega"]["value"]))
        if option_type in ["put", "both"] and "put" in result and "vega" in result["put"]:
            max_vega = max(max_vega, abs(result["put"]["vega"]["value"]))

        if max_vega > 0.3:
            risks["volatility_risk"] = "HIGH"
        elif max_vega < 0.1:
            risks["volatility_risk"] = "LOW"

        # Assess time decay risk (theta)
        max_theta = 0
        if option_type in ["call", "both"] and "call" in result and "theta" in result["call"]:
            max_theta = max(max_theta, abs(result["call"]["theta"]["value"]))
        if option_type in ["put", "both"] and "put" in result and "theta" in result["put"]:
            max_theta = max(max_theta, abs(result["put"]["theta"]["value"]))

        if max_theta > 0.1:
            risks["time_decay_risk"] = "HIGH"
        elif max_theta < 0.03:
            risks["time_decay_risk"] = "LOW"

        # Interest rate risk is generally low for short-dated options
        if result["time_to_expiry_days"] > 180:
            risks["interest_rate_risk"] = "MEDIUM"

        return risks
