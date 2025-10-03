"""
Alert System Tool - Monitor and alert on price movements and pattern detections
Configurable alerts for various market conditions
"""

import sys
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import pandas as pd


class AlertSystemTool:
    """Real-time alert system for price movements and pattern detection"""

    def __init__(self):
        self.data_dir = Path(__file__).parent.parent.parent.parent.parent / 'data' / 'stock-data'

    async def get_tool_info(self) -> Dict:
        """Get tool information for MCP protocol"""
        return {
            "name": "market.alert_system",
            "description": "Monitor stocks and create alerts for price movements, breakouts, and pattern detection",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock ticker symbol (e.g., AAPL, MSFT)"
                    },
                    "alert_type": {
                        "type": "string",
                        "enum": [
                            "price_target",
                            "percent_change",
                            "volume_spike",
                            "breakout",
                            "support_resistance",
                            "volatility",
                            "all"
                        ],
                        "description": "Type of alert to check"
                    },
                    "thresholds": {
                        "type": "object",
                        "description": "Alert thresholds (e.g., {\"price_above\": 150, \"price_below\": 100, \"percent_change\": 5})",
                        "properties": {
                            "price_above": {"type": "number"},
                            "price_below": {"type": "number"},
                            "percent_change": {"type": "number"},
                            "volume_multiplier": {"type": "number"},
                            "volatility_threshold": {"type": "number"}
                        }
                    }
                },
                "required": ["symbol", "alert_type"]
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

    def _check_price_target_alert(self, df: pd.DataFrame, thresholds: Dict) -> List[Dict]:
        """Check if price has crossed target levels"""
        alerts = []
        current_price = float(df.iloc[-1]['Close'])

        price_above = thresholds.get('price_above')
        price_below = thresholds.get('price_below')

        if price_above and current_price >= price_above:
            alerts.append({
                "type": "PRICE_TARGET_ABOVE",
                "severity": "MEDIUM",
                "message": f"Price {current_price:.2f} reached or exceeded target {price_above:.2f}",
                "current_price": current_price,
                "target_price": price_above,
                "timestamp": df.iloc[-1]['Date'].strftime('%Y-%m-%d')
            })

        if price_below and current_price <= price_below:
            alerts.append({
                "type": "PRICE_TARGET_BELOW",
                "severity": "MEDIUM",
                "message": f"Price {current_price:.2f} fell to or below target {price_below:.2f}",
                "current_price": current_price,
                "target_price": price_below,
                "timestamp": df.iloc[-1]['Date'].strftime('%Y-%m-%d')
            })

        return alerts

    def _check_percent_change_alert(self, df: pd.DataFrame, thresholds: Dict) -> List[Dict]:
        """Check for significant percentage changes"""
        alerts = []

        if len(df) < 2:
            return alerts

        # Daily change
        current_price = float(df.iloc[-1]['Close'])
        prev_price = float(df.iloc[-2]['Close'])
        daily_change_pct = ((current_price - prev_price) / prev_price) * 100

        # Weekly change (5 trading days)
        if len(df) >= 5:
            week_ago_price = float(df.iloc[-5]['Close'])
            weekly_change_pct = ((current_price - week_ago_price) / week_ago_price) * 100
        else:
            weekly_change_pct = 0

        threshold = thresholds.get('percent_change', 5)

        if abs(daily_change_pct) >= threshold:
            direction = "UP" if daily_change_pct > 0 else "DOWN"
            severity = "HIGH" if abs(daily_change_pct) >= threshold * 2 else "MEDIUM"

            alerts.append({
                "type": f"DAILY_CHANGE_{direction}",
                "severity": severity,
                "message": f"Daily change of {daily_change_pct:.2f}% exceeds threshold {threshold}%",
                "change_pct": daily_change_pct,
                "threshold": threshold,
                "timestamp": df.iloc[-1]['Date'].strftime('%Y-%m-%d')
            })

        if abs(weekly_change_pct) >= threshold * 2:
            direction = "UP" if weekly_change_pct > 0 else "DOWN"

            alerts.append({
                "type": f"WEEKLY_CHANGE_{direction}",
                "severity": "MEDIUM",
                "message": f"Weekly change of {weekly_change_pct:.2f}% is significant",
                "change_pct": weekly_change_pct,
                "timestamp": df.iloc[-1]['Date'].strftime('%Y-%m-%d')
            })

        return alerts

    def _check_volume_spike_alert(self, df: pd.DataFrame, thresholds: Dict) -> List[Dict]:
        """Check for unusual volume spikes"""
        alerts = []

        if 'Volume' not in df.columns or len(df) < 20:
            return alerts

        current_volume = int(df.iloc[-1]['Volume'])
        avg_volume = int(df['Volume'].tail(20).mean())

        threshold_multiplier = thresholds.get('volume_multiplier', 2.0)

        if current_volume >= avg_volume * threshold_multiplier:
            severity = "HIGH" if current_volume >= avg_volume * 3 else "MEDIUM"

            alerts.append({
                "type": "VOLUME_SPIKE",
                "severity": severity,
                "message": f"Volume {current_volume:,} is {current_volume/avg_volume:.1f}x average",
                "current_volume": current_volume,
                "avg_volume": avg_volume,
                "multiplier": float(current_volume / avg_volume),
                "timestamp": df.iloc[-1]['Date'].strftime('%Y-%m-%d')
            })

        return alerts

    def _check_breakout_alert(self, df: pd.DataFrame) -> List[Dict]:
        """Check for price breakouts from recent range"""
        alerts = []

        if len(df) < 20:
            return alerts

        # Calculate 20-day range
        recent_data = df.tail(20)
        range_high = float(recent_data['High'].max())
        range_low = float(recent_data['Low'].min())

        current_price = float(df.iloc[-1]['Close'])

        # Check for upside breakout
        if current_price > range_high * 1.01:  # 1% above range high
            pct_above = ((current_price - range_high) / range_high) * 100

            alerts.append({
                "type": "UPSIDE_BREAKOUT",
                "severity": "HIGH",
                "message": f"Price broke above 20-day high of {range_high:.2f}",
                "current_price": current_price,
                "breakout_level": range_high,
                "pct_above": pct_above,
                "timestamp": df.iloc[-1]['Date'].strftime('%Y-%m-%d')
            })

        # Check for downside breakdown
        if current_price < range_low * 0.99:  # 1% below range low
            pct_below = ((range_low - current_price) / range_low) * 100

            alerts.append({
                "type": "DOWNSIDE_BREAKDOWN",
                "severity": "HIGH",
                "message": f"Price broke below 20-day low of {range_low:.2f}",
                "current_price": current_price,
                "breakout_level": range_low,
                "pct_below": pct_below,
                "timestamp": df.iloc[-1]['Date'].strftime('%Y-%m-%d')
            })

        return alerts

    def _check_support_resistance_alert(self, df: pd.DataFrame) -> List[Dict]:
        """Check if price is near support or resistance levels"""
        alerts = []

        if len(df) < 50:
            return alerts

        # Find recent highs and lows
        recent_data = df.tail(50)
        resistance_level = float(recent_data['High'].max())
        support_level = float(recent_data['Low'].min())

        current_price = float(df.iloc[-1]['Close'])

        # Check proximity to resistance (within 2%)
        if resistance_level * 0.98 <= current_price <= resistance_level:
            alerts.append({
                "type": "NEAR_RESISTANCE",
                "severity": "MEDIUM",
                "message": f"Price approaching resistance at {resistance_level:.2f}",
                "current_price": current_price,
                "resistance_level": resistance_level,
                "distance_pct": ((resistance_level - current_price) / current_price) * 100,
                "timestamp": df.iloc[-1]['Date'].strftime('%Y-%m-%d')
            })

        # Check proximity to support (within 2%)
        if support_level <= current_price <= support_level * 1.02:
            alerts.append({
                "type": "NEAR_SUPPORT",
                "severity": "MEDIUM",
                "message": f"Price approaching support at {support_level:.2f}",
                "current_price": current_price,
                "support_level": support_level,
                "distance_pct": ((current_price - support_level) / current_price) * 100,
                "timestamp": df.iloc[-1]['Date'].strftime('%Y-%m-%d')
            })

        return alerts

    def _check_volatility_alert(self, df: pd.DataFrame, thresholds: Dict) -> List[Dict]:
        """Check for unusual volatility"""
        alerts = []

        if len(df) < 20:
            return alerts

        # Calculate recent volatility
        recent_data = df.tail(20)
        returns = recent_data['Close'].pct_change()
        current_vol = float(returns.std() * 100)

        # Calculate average volatility over longer period
        if len(df) >= 60:
            long_term_data = df.tail(60)
            long_term_returns = long_term_data['Close'].pct_change()
            avg_vol = float(long_term_returns.std() * 100)
        else:
            avg_vol = current_vol

        threshold = thresholds.get('volatility_threshold', 1.5)

        if current_vol >= avg_vol * threshold:
            severity = "HIGH" if current_vol >= avg_vol * 2 else "MEDIUM"

            alerts.append({
                "type": "HIGH_VOLATILITY",
                "severity": severity,
                "message": f"Volatility {current_vol:.2f}% is {current_vol/avg_vol:.1f}x normal",
                "current_volatility": current_vol,
                "avg_volatility": avg_vol,
                "multiplier": float(current_vol / avg_vol),
                "timestamp": df.iloc[-1]['Date'].strftime('%Y-%m-%d')
            })

        return alerts

    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute alert system checks"""
        symbol = arguments.get("symbol", "").upper()
        alert_type = arguments.get("alert_type", "all")
        thresholds = arguments.get("thresholds", {})

        if not symbol:
            return {"error": "Symbol is required"}

        # Load stock data
        df = self._load_stock_data(symbol)
        if df is None:
            return {
                "error": f"No data found for {symbol}",
                "suggestion": "Try symbols like AAPL, MSFT, GOOGL, etc."
            }

        # Get recent data (last 90 days)
        df_recent = df.tail(90)

        if len(df_recent) < 2:
            return {
                "error": f"Insufficient data for {symbol}",
                "available_days": len(df_recent)
            }

        # Collect all alerts
        all_alerts = []

        # Check alerts based on type
        if alert_type == "all" or alert_type == "price_target":
            all_alerts.extend(self._check_price_target_alert(df_recent, thresholds))

        if alert_type == "all" or alert_type == "percent_change":
            all_alerts.extend(self._check_percent_change_alert(df_recent, thresholds))

        if alert_type == "all" or alert_type == "volume_spike":
            all_alerts.extend(self._check_volume_spike_alert(df_recent, thresholds))

        if alert_type == "all" or alert_type == "breakout":
            all_alerts.extend(self._check_breakout_alert(df_recent))

        if alert_type == "all" or alert_type == "support_resistance":
            all_alerts.extend(self._check_support_resistance_alert(df_recent))

        if alert_type == "all" or alert_type == "volatility":
            all_alerts.extend(self._check_volatility_alert(df_recent, thresholds))

        # Get latest price info
        latest = df_recent.iloc[-1]

        # Count alerts by severity
        high_severity = sum(1 for a in all_alerts if a.get('severity') == 'HIGH')
        medium_severity = sum(1 for a in all_alerts if a.get('severity') == 'MEDIUM')

        return {
            "symbol": symbol,
            "current_price": float(latest['Close']),
            "last_updated": latest['Date'].strftime('%Y-%m-%d'),
            "alert_type": alert_type,
            "thresholds": thresholds,
            "alerts": {
                "total_count": len(all_alerts),
                "high_severity_count": high_severity,
                "medium_severity_count": medium_severity,
                "active_alerts": all_alerts
            },
            "summary": self._generate_summary(symbol, all_alerts, high_severity, medium_severity),
            "data_source": "Historical CSV data"
        }

    def _generate_summary(self, symbol: str, alerts: List[Dict],
                         high_count: int, medium_count: int) -> str:
        """Generate human-readable summary"""
        if not alerts:
            return f"{symbol}: No alerts triggered"

        summary_parts = []
        summary_parts.append(f"{symbol}: {len(alerts)} alert(s)")

        if high_count > 0:
            summary_parts.append(f"{high_count} HIGH severity")
        if medium_count > 0:
            summary_parts.append(f"{medium_count} MEDIUM severity")

        # Add most critical alert
        high_alerts = [a for a in alerts if a.get('severity') == 'HIGH']
        if high_alerts:
            critical = high_alerts[0]
            summary_parts.append(f"⚠️ {critical['type']}: {critical['message']}")
        elif alerts:
            summary_parts.append(f"ℹ️ {alerts[0]['type']}")

        return " | ".join(summary_parts)


# Export for MCP server
__all__ = ['AlertSystemTool']
