"""
Pattern Recognition Tool - Chart pattern detection and trend analysis
Detects support/resistance levels, trendlines, and chart patterns
"""

import sys
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from scipy.signal import argrelextrema
from scipy.stats import linregress


class PatternRecognitionTool:
    """Advanced pattern recognition for technical chart analysis"""

    def __init__(self):
        self.data_dir = Path(__file__).parent.parent.parent.parent.parent / 'data' / 'stock-data'

    async def get_tool_info(self) -> Dict:
        """Get tool information for MCP protocol"""
        return {
            "name": "market.pattern_recognition",
            "description": "Detect chart patterns, support/resistance levels, and trend analysis",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock ticker symbol (e.g., AAPL, MSFT)"
                    },
                    "period": {
                        "type": "integer",
                        "description": "Number of days for analysis (default: 60)",
                        "default": 60
                    },
                    "patterns": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["trend", "support_resistance", "head_shoulders", "double_top_bottom", "triangle", "all"]
                        },
                        "description": "Patterns to detect (default: all)",
                        "default": ["all"]
                    }
                },
                "required": ["symbol"]
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

    def _detect_trend(self, df: pd.DataFrame) -> Dict:
        """Detect overall trend using linear regression"""
        prices = df['Close'].values
        x = np.arange(len(prices))

        slope, intercept, r_value, p_value, std_err = linregress(x, prices)

        # Determine trend strength
        r_squared = r_value ** 2

        if slope > 0:
            trend_direction = "UPTREND"
        elif slope < 0:
            trend_direction = "DOWNTREND"
        else:
            trend_direction = "SIDEWAYS"

        # Strength based on R-squared
        if r_squared > 0.7:
            strength = "STRONG"
        elif r_squared > 0.4:
            strength = "MODERATE"
        else:
            strength = "WEAK"

        # Calculate trend line
        trend_line = slope * x + intercept

        return {
            "direction": trend_direction,
            "strength": strength,
            "slope": float(slope),
            "r_squared": float(r_squared),
            "start_price": float(trend_line[0]),
            "end_price": float(trend_line[-1]),
            "price_change_pct": float((trend_line[-1] - trend_line[0]) / trend_line[0] * 100)
        }

    def _find_support_resistance(self, df: pd.DataFrame, order: int = 5) -> Dict:
        """Find support and resistance levels using local extrema"""
        highs = df['High'].values
        lows = df['Low'].values

        # Find local maxima (resistance) and minima (support)
        resistance_indices = argrelextrema(highs, np.greater, order=order)[0]
        support_indices = argrelextrema(lows, np.less, order=order)[0]

        # Get resistance levels
        resistance_levels = []
        for idx in resistance_indices[-5:]:  # Last 5 resistance points
            resistance_levels.append({
                "price": float(df.iloc[idx]['High']),
                "date": df.iloc[idx]['Date'].strftime('%Y-%m-%d'),
                "type": "resistance"
            })

        # Get support levels
        support_levels = []
        for idx in support_indices[-5:]:  # Last 5 support points
            support_levels.append({
                "price": float(df.iloc[idx]['Low']),
                "date": df.iloc[idx]['Date'].strftime('%Y-%m-%d'),
                "type": "support"
            })

        # Current price position
        current_price = float(df.iloc[-1]['Close'])

        # Find nearest support and resistance
        nearest_support = None
        nearest_resistance = None

        if support_levels:
            supports_below = [s for s in support_levels if s['price'] < current_price]
            if supports_below:
                nearest_support = max(supports_below, key=lambda x: x['price'])

        if resistance_levels:
            resistances_above = [r for r in resistance_levels if r['price'] > current_price]
            if resistances_above:
                nearest_resistance = min(resistances_above, key=lambda x: x['price'])

        return {
            "current_price": current_price,
            "nearest_support": nearest_support,
            "nearest_resistance": nearest_resistance,
            "all_support_levels": sorted(support_levels, key=lambda x: x['price'], reverse=True),
            "all_resistance_levels": sorted(resistance_levels, key=lambda x: x['price'])
        }

    def _detect_head_shoulders(self, df: pd.DataFrame) -> Optional[Dict]:
        """Detect head and shoulders pattern"""
        highs = df['High'].values

        # Find peaks
        peaks = argrelextrema(highs, np.greater, order=5)[0]

        if len(peaks) < 3:
            return None

        # Check last 3 peaks for head and shoulders
        last_peaks = peaks[-3:]
        peak_prices = [highs[i] for i in last_peaks]

        # Head and shoulders: middle peak should be highest
        if peak_prices[1] > peak_prices[0] and peak_prices[1] > peak_prices[2]:
            # Check if shoulders are roughly equal (within 5%)
            shoulder_diff = abs(peak_prices[0] - peak_prices[2]) / peak_prices[0]

            if shoulder_diff < 0.05:
                return {
                    "pattern": "HEAD_AND_SHOULDERS",
                    "left_shoulder": float(peak_prices[0]),
                    "head": float(peak_prices[1]),
                    "right_shoulder": float(peak_prices[2]),
                    "confidence": "HIGH" if shoulder_diff < 0.02 else "MODERATE",
                    "signal": "BEARISH - Potential reversal"
                }

        # Inverse head and shoulders on lows
        lows = df['Low'].values
        troughs = argrelextrema(lows, np.less, order=5)[0]

        if len(troughs) >= 3:
            last_troughs = troughs[-3:]
            trough_prices = [lows[i] for i in last_troughs]

            if trough_prices[1] < trough_prices[0] and trough_prices[1] < trough_prices[2]:
                shoulder_diff = abs(trough_prices[0] - trough_prices[2]) / trough_prices[0]

                if shoulder_diff < 0.05:
                    return {
                        "pattern": "INVERSE_HEAD_AND_SHOULDERS",
                        "left_shoulder": float(trough_prices[0]),
                        "head": float(trough_prices[1]),
                        "right_shoulder": float(trough_prices[2]),
                        "confidence": "HIGH" if shoulder_diff < 0.02 else "MODERATE",
                        "signal": "BULLISH - Potential reversal"
                    }

        return None

    def _detect_double_top_bottom(self, df: pd.DataFrame) -> Optional[Dict]:
        """Detect double top or double bottom patterns"""
        highs = df['High'].values
        lows = df['Low'].values

        # Find peaks for double top
        peaks = argrelextrema(highs, np.greater, order=5)[0]

        if len(peaks) >= 2:
            last_two_peaks = peaks[-2:]
            peak_prices = [highs[i] for i in last_two_peaks]

            # Check if peaks are roughly equal (within 3%)
            price_diff = abs(peak_prices[0] - peak_prices[1]) / peak_prices[0]

            if price_diff < 0.03:
                return {
                    "pattern": "DOUBLE_TOP",
                    "first_peak": float(peak_prices[0]),
                    "second_peak": float(peak_prices[1]),
                    "difference_pct": float(price_diff * 100),
                    "confidence": "HIGH" if price_diff < 0.01 else "MODERATE",
                    "signal": "BEARISH - Reversal likely"
                }

        # Find troughs for double bottom
        troughs = argrelextrema(lows, np.less, order=5)[0]

        if len(troughs) >= 2:
            last_two_troughs = troughs[-2:]
            trough_prices = [lows[i] for i in last_two_troughs]

            price_diff = abs(trough_prices[0] - trough_prices[1]) / trough_prices[0]

            if price_diff < 0.03:
                return {
                    "pattern": "DOUBLE_BOTTOM",
                    "first_bottom": float(trough_prices[0]),
                    "second_bottom": float(trough_prices[1]),
                    "difference_pct": float(price_diff * 100),
                    "confidence": "HIGH" if price_diff < 0.01 else "MODERATE",
                    "signal": "BULLISH - Reversal likely"
                }

        return None

    def _detect_triangle(self, df: pd.DataFrame) -> Optional[Dict]:
        """Detect triangle patterns (ascending, descending, symmetrical)"""
        highs = df['High'].values
        lows = df['Low'].values

        # Get peaks and troughs
        peaks = argrelextrema(highs, np.greater, order=3)[0]
        troughs = argrelextrema(lows, np.less, order=3)[0]

        if len(peaks) < 2 or len(troughs) < 2:
            return None

        # Analyze last few peaks and troughs
        recent_peaks = peaks[-3:] if len(peaks) >= 3 else peaks[-2:]
        recent_troughs = troughs[-3:] if len(troughs) >= 3 else troughs[-2:]

        # Calculate trendlines
        peak_slope, _, peak_r, _, _ = linregress(recent_peaks, highs[recent_peaks])
        trough_slope, _, trough_r, _, _ = linregress(recent_troughs, lows[recent_troughs])

        # Determine triangle type
        if abs(peak_slope) < 0.01 and trough_slope > 0.01:
            # Ascending triangle (flat top, rising bottom)
            return {
                "pattern": "ASCENDING_TRIANGLE",
                "upper_trendline_slope": float(peak_slope),
                "lower_trendline_slope": float(trough_slope),
                "signal": "BULLISH - Breakout likely upward",
                "confidence": "HIGH" if abs(peak_r) > 0.7 and abs(trough_r) > 0.7 else "MODERATE"
            }
        elif peak_slope < -0.01 and abs(trough_slope) < 0.01:
            # Descending triangle (declining top, flat bottom)
            return {
                "pattern": "DESCENDING_TRIANGLE",
                "upper_trendline_slope": float(peak_slope),
                "lower_trendline_slope": float(trough_slope),
                "signal": "BEARISH - Breakout likely downward",
                "confidence": "HIGH" if abs(peak_r) > 0.7 and abs(trough_r) > 0.7 else "MODERATE"
            }
        elif peak_slope < -0.01 and trough_slope > 0.01:
            # Symmetrical triangle (converging lines)
            return {
                "pattern": "SYMMETRICAL_TRIANGLE",
                "upper_trendline_slope": float(peak_slope),
                "lower_trendline_slope": float(trough_slope),
                "signal": "NEUTRAL - Breakout direction uncertain",
                "confidence": "MODERATE"
            }

        return None

    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute pattern recognition analysis"""
        symbol = arguments.get("symbol", "").upper()
        period = arguments.get("period", 60)
        requested_patterns = arguments.get("patterns", ["all"])

        if not symbol:
            return {"error": "Symbol is required"}

        # Load stock data
        df = self._load_stock_data(symbol)
        if df is None:
            return {
                "error": f"No data found for {symbol}",
                "suggestion": "Try symbols like AAPL, MSFT, GOOGL, etc."
            }

        # Get recent data
        df_recent = df.tail(period)

        if len(df_recent) < 20:
            return {
                "error": f"Insufficient data for {symbol}",
                "available_days": len(df_recent)
            }

        # Determine which patterns to detect
        detect_all = "all" in requested_patterns
        results = {}

        # Detect trend
        if detect_all or "trend" in requested_patterns:
            results["trend"] = self._detect_trend(df_recent)

        # Find support/resistance
        if detect_all or "support_resistance" in requested_patterns:
            results["support_resistance"] = self._find_support_resistance(df_recent)

        # Detect head and shoulders
        if detect_all or "head_shoulders" in requested_patterns:
            hs_pattern = self._detect_head_shoulders(df_recent)
            if hs_pattern:
                results["head_shoulders"] = hs_pattern
            else:
                results["head_shoulders"] = {"pattern": "NOT_DETECTED"}

        # Detect double top/bottom
        if detect_all or "double_top_bottom" in requested_patterns:
            dt_pattern = self._detect_double_top_bottom(df_recent)
            if dt_pattern:
                results["double_top_bottom"] = dt_pattern
            else:
                results["double_top_bottom"] = {"pattern": "NOT_DETECTED"}

        # Detect triangle
        if detect_all or "triangle" in requested_patterns:
            triangle_pattern = self._detect_triangle(df_recent)
            if triangle_pattern:
                results["triangle"] = triangle_pattern
            else:
                results["triangle"] = {"pattern": "NOT_DETECTED"}

        # Get latest price info
        latest = df_recent.iloc[-1]

        return {
            "symbol": symbol,
            "date": latest['Date'].strftime('%Y-%m-%d'),
            "current_price": float(latest['Close']),
            "analysis_period_days": len(df_recent),
            "patterns": results,
            "summary": self._generate_summary(results),
            "data_source": "Historical CSV data"
        }

    def _generate_summary(self, patterns: Dict) -> str:
        """Generate human-readable summary"""
        summary_parts = []

        if "trend" in patterns:
            trend = patterns["trend"]
            summary_parts.append(f"Trend: {trend['strength']} {trend['direction']}")

        if "support_resistance" in patterns:
            sr = patterns["support_resistance"]
            if sr.get("nearest_support"):
                summary_parts.append(f"Support: ${sr['nearest_support']['price']:.2f}")
            if sr.get("nearest_resistance"):
                summary_parts.append(f"Resistance: ${sr['nearest_resistance']['price']:.2f}")

        # Add detected patterns
        for key, value in patterns.items():
            if key not in ["trend", "support_resistance"]:
                if isinstance(value, dict) and value.get("pattern") != "NOT_DETECTED":
                    pattern_name = value.get("pattern", "Unknown")
                    signal = value.get("signal", "")
                    summary_parts.append(f"{pattern_name}: {signal}")

        if not summary_parts:
            return "No significant patterns detected"

        return " | ".join(summary_parts)


# Export for MCP server
__all__ = ['PatternRecognitionTool']
