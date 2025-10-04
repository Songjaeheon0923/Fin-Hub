"""
Anomaly Detection Tool - Statistical anomaly detection for price movements
Uses Z-Score, IQR, and statistical methods to detect unusual price/volume behavior
"""

import sys
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
from pathlib import Path
from scipy import stats


class AnomalyDetectionTool:
    """Detect anomalies in price and volume data using statistical methods"""

    def __init__(self):
        self.data_dir = Path(__file__).parent.parent.parent.parent.parent / 'data' / 'stock-data'

    async def get_tool_info(self) -> Dict:
        """Get tool information for MCP protocol"""
        return {
            "name": "anomaly_detection",
            "description": "Detect price and volume anomalies using statistical methods (Z-Score, IQR, Volatility)",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock ticker symbol (e.g., AAPL, MSFT)"
                    },
                    "period": {
                        "type": "integer",
                        "description": "Number of days for analysis (default: 90)",
                        "default": 90
                    },
                    "sensitivity": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "Detection sensitivity (default: medium)",
                        "default": "medium"
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

    def _get_threshold(self, sensitivity: str) -> float:
        """Get Z-score threshold based on sensitivity"""
        thresholds = {
            "low": 3.0,      # 99.7% of data within range
            "medium": 2.5,   # 98.8% of data within range
            "high": 2.0      # 95.4% of data within range
        }
        return thresholds.get(sensitivity, 2.5)

    def _detect_price_anomalies_zscore(self, df: pd.DataFrame, threshold: float) -> List[Dict]:
        """Detect price anomalies using Z-Score method"""
        df = df.copy()  # Create copy to avoid SettingWithCopyWarning
        df['Price_Change_Pct'] = df['Close'].pct_change() * 100

        # Calculate Z-Score only on non-null values
        price_changes = df['Price_Change_Pct'].dropna()
        if len(price_changes) > 0:
            z_scores = np.abs(stats.zscore(price_changes))
            # Create a Series with proper index alignment
            df.loc[price_changes.index, 'Z_Score'] = z_scores
        else:
            df['Z_Score'] = np.nan

        anomalies = []
        for idx, row in df.iterrows():
            if pd.notna(row['Z_Score']) and row['Z_Score'] > threshold:
                anomalies.append({
                    "date": row['Date'].strftime('%Y-%m-%d'),
                    "price": float(row['Close']),
                    "change_pct": float(row['Price_Change_Pct']),
                    "z_score": float(row['Z_Score']),
                    "severity": "HIGH" if row['Z_Score'] > threshold + 1 else "MEDIUM",
                    "type": "SPIKE" if row['Price_Change_Pct'] > 0 else "DROP"
                })

        return sorted(anomalies, key=lambda x: abs(x['z_score']), reverse=True)[:10]

    def _detect_volume_anomalies(self, df: pd.DataFrame, threshold: float) -> List[Dict]:
        """Detect volume anomalies"""
        if 'Volume' not in df.columns:
            return []

        df = df.copy()
        volumes = df['Volume'].dropna()
        if len(volumes) > 0:
            z_scores = np.abs(stats.zscore(volumes))
            df.loc[volumes.index, 'Volume_Z_Score'] = z_scores
        else:
            df['Volume_Z_Score'] = np.nan

        anomalies = []
        for idx, row in df.iterrows():
            if pd.notna(row['Volume_Z_Score']) and row['Volume_Z_Score'] > threshold:
                # Calculate average volume
                avg_volume = df['Volume'].mean()

                anomalies.append({
                    "date": row['Date'].strftime('%Y-%m-%d'),
                    "volume": int(row['Volume']),
                    "avg_volume": int(avg_volume),
                    "volume_ratio": float(row['Volume'] / avg_volume),
                    "z_score": float(row['Volume_Z_Score']),
                    "severity": "HIGH" if row['Volume_Z_Score'] > threshold + 1 else "MEDIUM"
                })

        return sorted(anomalies, key=lambda x: x['z_score'], reverse=True)[:10]

    def _detect_volatility_anomalies(self, df: pd.DataFrame, window: int = 20) -> List[Dict]:
        """Detect unusual volatility periods"""
        df = df.copy()
        df['Returns'] = df['Close'].pct_change()
        df['Volatility'] = df['Returns'].rolling(window=window).std() * np.sqrt(252) * 100

        # Z-score of volatility
        volatilities = df['Volatility'].dropna()
        if len(volatilities) > 0:
            z_scores = np.abs(stats.zscore(volatilities))
            df.loc[volatilities.index, 'Vol_Z_Score'] = z_scores
        else:
            df['Vol_Z_Score'] = np.nan

        anomalies = []
        avg_volatility = df['Volatility'].mean()

        for idx, row in df.iterrows():
            if pd.notna(row['Vol_Z_Score']) and row['Vol_Z_Score'] > 2.0:
                anomalies.append({
                    "date": row['Date'].strftime('%Y-%m-%d'),
                    "volatility": float(row['Volatility']),
                    "avg_volatility": float(avg_volatility),
                    "z_score": float(row['Vol_Z_Score']),
                    "severity": "HIGH" if row['Volatility'] > avg_volatility * 2 else "MEDIUM"
                })

        return sorted(anomalies, key=lambda x: x['z_score'], reverse=True)[:10]

    def _detect_gap_anomalies(self, df: pd.DataFrame) -> List[Dict]:
        """Detect price gaps (gap up/down at market open)"""
        df = df.copy()
        df['Gap'] = ((df['Open'] - df['Close'].shift(1)) / df['Close'].shift(1)) * 100
        df_reset = df.reset_index(drop=True)

        anomalies = []
        for i in range(1, len(df_reset)):  # Start from 1 to have previous close
            row = df_reset.iloc[i]
            if pd.notna(row['Gap']) and abs(row['Gap']) > 2.0:  # More than 2% gap
                prev_row = df_reset.iloc[i-1]
                anomalies.append({
                    "date": row['Date'].strftime('%Y-%m-%d'),
                    "gap_pct": float(row['Gap']),
                    "prev_close": float(prev_row['Close']),
                    "open": float(row['Open']),
                    "type": "GAP_UP" if row['Gap'] > 0 else "GAP_DOWN",
                    "severity": "HIGH" if abs(row['Gap']) > 5 else "MEDIUM"
                })

        return sorted(anomalies, key=lambda x: abs(x['gap_pct']), reverse=True)[:10]

    def _detect_range_breakouts(self, df: pd.DataFrame, window: int = 20) -> List[Dict]:
        """Detect breakouts from normal trading range"""
        df = df.copy()
        df['Upper_Range'] = df['High'].rolling(window=window).max()
        df['Lower_Range'] = df['Low'].rolling(window=window).min()

        anomalies = []
        df_reset = df.reset_index(drop=True)

        for i in range(window, len(df_reset)):
            row = df_reset.iloc[i]
            prev_upper = df_reset.iloc[i-1]['Upper_Range']
            prev_lower = df_reset.iloc[i-1]['Lower_Range']

            if pd.isna(prev_upper) or pd.isna(prev_lower):
                continue

            # Breakout above range
            if row['Close'] > prev_upper:
                pct_above = ((row['Close'] - prev_upper) / prev_upper) * 100
                if pct_above > 1:  # More than 1% above range
                    anomalies.append({
                        "date": row['Date'].strftime('%Y-%m-%d'),
                        "price": float(row['Close']),
                        "range_level": float(prev_upper),
                        "breakout_pct": float(pct_above),
                        "type": "UPSIDE_BREAKOUT",
                        "severity": "HIGH" if pct_above > 3 else "MEDIUM"
                    })

            # Breakdown below range
            if row['Close'] < prev_lower:
                pct_below = ((prev_lower - row['Close']) / prev_lower) * 100
                if pct_below > 1:
                    anomalies.append({
                        "date": row['Date'].strftime('%Y-%m-%d'),
                        "price": float(row['Close']),
                        "range_level": float(prev_lower),
                        "breakout_pct": float(-pct_below),
                        "type": "DOWNSIDE_BREAKDOWN",
                        "severity": "HIGH" if pct_below > 3 else "MEDIUM"
                    })

        return sorted(anomalies, key=lambda x: abs(x['breakout_pct']), reverse=True)[:10]

    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute anomaly detection analysis"""
        symbol = arguments.get("symbol", "").upper()
        period = arguments.get("period", 90)
        sensitivity = arguments.get("sensitivity", "medium")

        if not symbol:
            return {"error": "Symbol is required"}

        # Load stock data
        df = self._load_stock_data(symbol)
        if df is None:
            return {
                "error": f"No data found for {symbol}",
                "suggestion": "Try symbols like AAPL, MSFT, GOOGL, etc."
            }

        # Get recent data (plus extra for statistical calculations)
        df_recent = df.tail(period + 50)

        if len(df_recent) < 30:
            return {
                "error": f"Insufficient data for {symbol}",
                "available_days": len(df_recent)
            }

        # Get threshold based on sensitivity
        threshold = self._get_threshold(sensitivity)

        # Detect various anomalies
        price_anomalies = self._detect_price_anomalies_zscore(df_recent, threshold)
        volume_anomalies = self._detect_volume_anomalies(df_recent, threshold)
        volatility_anomalies = self._detect_volatility_anomalies(df_recent)
        gap_anomalies = self._detect_gap_anomalies(df_recent)
        breakout_anomalies = self._detect_range_breakouts(df_recent)

        # Get latest stats
        latest = df_recent.iloc[-1]
        recent_volatility = df_recent['Close'].pct_change().std() * np.sqrt(252) * 100

        # Count anomalies by severity
        all_anomalies = (price_anomalies + volume_anomalies + volatility_anomalies +
                        gap_anomalies + breakout_anomalies)

        high_severity_count = sum(1 for a in all_anomalies if a.get('severity') == 'HIGH')
        medium_severity_count = sum(1 for a in all_anomalies if a.get('severity') == 'MEDIUM')

        return {
            "symbol": symbol,
            "date": latest['Date'].strftime('%Y-%m-%d'),
            "current_price": float(latest['Close']),
            "analysis_period_days": len(df_recent),
            "sensitivity": sensitivity,
            "statistics": {
                "current_volatility_pct": float(recent_volatility),
                "avg_daily_change_pct": float(df_recent['Close'].pct_change().mean() * 100),
                "total_anomalies_detected": len(all_anomalies),
                "high_severity_count": high_severity_count,
                "medium_severity_count": medium_severity_count
            },
            "anomalies": {
                "price_anomalies": price_anomalies[:5],
                "volume_anomalies": volume_anomalies[:5],
                "volatility_anomalies": volatility_anomalies[:5],
                "gap_anomalies": gap_anomalies[:5],
                "breakout_anomalies": breakout_anomalies[:5]
            },
            "summary": self._generate_summary(all_anomalies, high_severity_count, medium_severity_count),
            "data_source": "Historical CSV data"
        }

    def _generate_summary(self, all_anomalies: List[Dict], high_count: int, medium_count: int) -> str:
        """Generate human-readable summary"""
        if not all_anomalies:
            return "No significant anomalies detected in the analysis period"

        summary_parts = []
        summary_parts.append(f"Total anomalies: {len(all_anomalies)}")
        summary_parts.append(f"High severity: {high_count}")
        summary_parts.append(f"Medium severity: {medium_count}")

        # Recent anomaly
        if all_anomalies:
            most_recent = max(all_anomalies, key=lambda x: x['date'])
            anomaly_type = most_recent.get('type', 'Unknown')
            summary_parts.append(f"Most recent: {anomaly_type} on {most_recent['date']}")

        return " | ".join(summary_parts)


# Export for MCP server
__all__ = ['AnomalyDetectionTool']
