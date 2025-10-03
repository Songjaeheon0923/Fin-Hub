#!/usr/bin/env python3
"""
Fin-Hub Data Validation and Analysis Script
Validates and analyzes all downloaded financial data
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
STOCK_DATA_DIR = PROJECT_ROOT / "data" / "stock-data"
CRYPTO_DATA_DIR = PROJECT_ROOT / "data" / "crypto-cache"
GEKKO_DATA_DIR = PROJECT_ROOT / "data" / "gekko-history"

# Color codes
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class DataValidator:
    """Validates financial data integrity and quality"""

    def __init__(self):
        self.results = {
            "stocks": {"validated": 0, "errors": 0, "warnings": 0, "details": []},
            "crypto": {"validated": 0, "errors": 0, "warnings": 0, "details": []},
            "gekko": {"validated": 0, "errors": 0, "warnings": 0, "details": []},
        }

    def validate_stock_data(self) -> Dict:
        """Validate S&P 500 stock data"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}Validating Stock Data...{Colors.RESET}")

        if not STOCK_DATA_DIR.exists():
            print(f"{Colors.RED}[ERROR] Stock data directory not found{Colors.RESET}")
            return self.results["stocks"]

        csv_files = list(STOCK_DATA_DIR.glob("*.csv"))
        csv_files = [f for f in csv_files if not f.name.startswith("_")]

        print(f"{Colors.BLUE}[INFO] Found {len(csv_files)} stock files{Colors.RESET}")

        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file, index_col=0, parse_dates=True)

                # Validation checks
                issues = []

                # Check if empty
                if df.empty:
                    issues.append("Empty dataframe")

                # Check required columns
                required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
                missing_cols = [col for col in required_cols if col not in df.columns]
                if missing_cols:
                    issues.append(f"Missing columns: {missing_cols}")

                # Check for null values
                null_counts = df.isnull().sum()
                if null_counts.sum() > 0:
                    issues.append(f"Null values: {null_counts[null_counts > 0].to_dict()}")

                # Check date range
                if not df.empty:
                    days_of_data = (df.index.max() - df.index.min()).days
                    if days_of_data < 365:
                        issues.append(f"Insufficient data: {days_of_data} days")

                # Record results
                if issues:
                    self.results["stocks"]["warnings"] += 1
                    self.results["stocks"]["details"].append({
                        "file": csv_file.name,
                        "status": "warning",
                        "issues": issues,
                        "rows": len(df)
                    })
                else:
                    self.results["stocks"]["validated"] += 1

            except Exception as e:
                self.results["stocks"]["errors"] += 1
                self.results["stocks"]["details"].append({
                    "file": csv_file.name,
                    "status": "error",
                    "error": str(e)
                })

        return self.results["stocks"]

    def validate_crypto_data(self) -> Dict:
        """Validate cryptocurrency data"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}Validating Crypto Data...{Colors.RESET}")

        if not CRYPTO_DATA_DIR.exists():
            print(f"{Colors.YELLOW}[WARN] Crypto data directory not found{Colors.RESET}")
            return self.results["crypto"]

        json_files = list(CRYPTO_DATA_DIR.glob("*.json"))
        json_files = [f for f in json_files if not f.name.startswith("_")]

        print(f"{Colors.BLUE}[INFO] Found {len(json_files)} crypto files{Colors.RESET}")

        for json_file in json_files:
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)

                issues = []

                # Check data structure
                if not data:
                    issues.append("Empty data")
                elif isinstance(data, dict):
                    if 'prices' in data:
                        if len(data['prices']) < 30:
                            issues.append(f"Insufficient price data: {len(data['prices'])} points")
                    else:
                        issues.append("No price data found")

                if issues:
                    self.results["crypto"]["warnings"] += 1
                    self.results["crypto"]["details"].append({
                        "file": json_file.name,
                        "status": "warning",
                        "issues": issues
                    })
                else:
                    self.results["crypto"]["validated"] += 1

            except Exception as e:
                self.results["crypto"]["errors"] += 1
                self.results["crypto"]["details"].append({
                    "file": json_file.name,
                    "status": "error",
                    "error": str(e)
                })

        return self.results["crypto"]

    def validate_gekko_data(self) -> Dict:
        """Validate Gekko database files"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}Validating Gekko Data...{Colors.RESET}")

        if not GEKKO_DATA_DIR.exists():
            print(f"{Colors.YELLOW}[WARN] Gekko data directory not found (optional){Colors.RESET}")
            return self.results["gekko"]

        db_files = list(GEKKO_DATA_DIR.glob("*.db"))

        if not db_files:
            print(f"{Colors.YELLOW}[WARN] No Gekko database files found{Colors.RESET}")
            return self.results["gekko"]

        print(f"{Colors.BLUE}[INFO] Found {len(db_files)} Gekko databases{Colors.RESET}")

        import sqlite3

        for db_file in db_files:
            try:
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()

                # Get table count
                cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                table_count = cursor.fetchone()[0]

                issues = []

                if table_count == 0:
                    issues.append("No tables found")

                conn.close()

                if issues:
                    self.results["gekko"]["warnings"] += 1
                    self.results["gekko"]["details"].append({
                        "file": db_file.name,
                        "status": "warning",
                        "issues": issues,
                        "tables": table_count
                    })
                else:
                    self.results["gekko"]["validated"] += 1

            except Exception as e:
                self.results["gekko"]["errors"] += 1
                self.results["gekko"]["details"].append({
                    "file": db_file.name,
                    "status": "error",
                    "error": str(e)
                })

        return self.results["gekko"]

    def print_summary(self):
        """Print validation summary"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'Validation Summary':^60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}\n")

        for data_type, result in self.results.items():
            print(f"{Colors.BOLD}{data_type.upper()}:{Colors.RESET}")
            print(f"  {Colors.GREEN}[OK] Validated: {result['validated']}{Colors.RESET}")
            if result['warnings'] > 0:
                print(f"  {Colors.YELLOW}[WARN] Warnings: {result['warnings']}{Colors.RESET}")
            if result['errors'] > 0:
                print(f"  {Colors.RED}[ERROR] Errors: {result['errors']}{Colors.RESET}")

            # Show sample issues
            if result['details']:
                print(f"\n  {Colors.BOLD}Sample issues:{Colors.RESET}")
                for detail in result['details'][:3]:
                    status_color = Colors.GREEN if detail['status'] == 'ok' else (
                        Colors.YELLOW if detail['status'] == 'warning' else Colors.RED
                    )
                    print(f"    {status_color}{detail['file']}: {detail.get('issues', detail.get('error'))}{Colors.RESET}")
            print()


class DataAnalyzer:
    """Analyzes financial data and generates insights"""

    def __init__(self):
        self.analysis = {
            "stocks": {},
            "crypto": {},
            "summary": {}
        }

    def analyze_stock_data(self) -> Dict:
        """Analyze S&P 500 stock data"""
        print(f"\n{Colors.BOLD}{Colors.MAGENTA}Analyzing Stock Data...{Colors.RESET}")

        csv_files = list(STOCK_DATA_DIR.glob("*.csv"))
        csv_files = [f for f in csv_files if not f.name.startswith("_")]

        if not csv_files:
            return {}

        # Analyze top 10 stocks
        top_stocks = csv_files[:10]
        stock_stats = []

        for csv_file in top_stocks:
            try:
                df = pd.read_csv(csv_file, index_col=0, parse_dates=True)

                if df.empty or 'Close' not in df.columns:
                    continue

                ticker = csv_file.stem

                # Calculate statistics
                latest_price = df['Close'].iloc[-1]
                first_price = df['Close'].iloc[0]
                returns = ((latest_price - first_price) / first_price) * 100
                volatility = df['Close'].pct_change().std() * np.sqrt(252) * 100

                stock_stats.append({
                    "ticker": ticker,
                    "latest_price": latest_price,
                    "5y_returns": returns,
                    "volatility": volatility,
                    "records": len(df)
                })

            except Exception as e:
                print(f"{Colors.YELLOW}[WARN] Error analyzing {csv_file.name}: {e}{Colors.RESET}")

        # Sort by returns
        stock_stats.sort(key=lambda x: x['5y_returns'], reverse=True)

        self.analysis["stocks"] = {
            "total_stocks": len(csv_files),
            "analyzed": len(stock_stats),
            "top_performers": stock_stats[:5],
            "worst_performers": stock_stats[-5:]
        }

        return self.analysis["stocks"]

    def analyze_crypto_data(self) -> Dict:
        """Analyze cryptocurrency data"""
        print(f"\n{Colors.BOLD}{Colors.MAGENTA}Analyzing Crypto Data...{Colors.RESET}")

        json_files = list(CRYPTO_DATA_DIR.glob("*_data.json"))

        if not json_files:
            return {}

        crypto_stats = []

        for json_file in json_files:
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)

                if 'prices' not in data:
                    continue

                coin_name = json_file.stem.replace('_data', '')
                prices = [p[1] for p in data['prices']]

                if len(prices) < 2:
                    continue

                latest_price = prices[-1]
                first_price = prices[0]
                returns = ((latest_price - first_price) / first_price) * 100
                volatility = pd.Series(prices).pct_change().std() * np.sqrt(365) * 100

                crypto_stats.append({
                    "coin": coin_name,
                    "latest_price": latest_price,
                    "returns": returns,
                    "volatility": volatility,
                    "data_points": len(prices)
                })

            except Exception as e:
                print(f"{Colors.YELLOW}[WARN] Error analyzing {json_file.name}: {e}{Colors.RESET}")

        self.analysis["crypto"] = {
            "total_coins": len(json_files),
            "analyzed": len(crypto_stats),
            "statistics": crypto_stats
        }

        return self.analysis["crypto"]

    def print_analysis(self):
        """Print analysis results"""
        print(f"\n{Colors.BOLD}{Colors.MAGENTA}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.MAGENTA}{'Data Analysis Report':^60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.MAGENTA}{'='*60}{Colors.RESET}\n")

        # Stock analysis
        if self.analysis["stocks"]:
            stocks = self.analysis["stocks"]
            print(f"{Colors.BOLD}STOCK ANALYSIS:{Colors.RESET}")
            print(f"  Total stocks: {stocks['total_stocks']}")
            print(f"  Analyzed: {stocks['analyzed']}\n")

            if stocks.get('top_performers'):
                print(f"  {Colors.GREEN}Top 5 Performers (5Y):{Colors.RESET}")
                for stock in stocks['top_performers']:
                    print(f"    {stock['ticker']}: ${stock['latest_price']:.2f} "
                          f"({stock['5y_returns']:+.2f}%, Vol: {stock['volatility']:.2f}%)")

            if stocks.get('worst_performers'):
                print(f"\n  {Colors.RED}Bottom 5 Performers (5Y):{Colors.RESET}")
                for stock in stocks['worst_performers']:
                    print(f"    {stock['ticker']}: ${stock['latest_price']:.2f} "
                          f"({stock['5y_returns']:+.2f}%, Vol: {stock['volatility']:.2f}%)")

        # Crypto analysis
        if self.analysis["crypto"]:
            crypto = self.analysis["crypto"]
            print(f"\n{Colors.BOLD}CRYPTO ANALYSIS:{Colors.RESET}")
            print(f"  Total coins: {crypto['total_coins']}")
            print(f"  Analyzed: {crypto['analyzed']}\n")

            if crypto.get('statistics'):
                print(f"  {Colors.CYAN}Cryptocurrency Statistics:{Colors.RESET}")
                for coin_stat in crypto['statistics']:
                    print(f"    {coin_stat['coin'].upper()}: ${coin_stat['latest_price']:,.2f} "
                          f"({coin_stat['returns']:+.2f}%, Vol: {coin_stat['volatility']:.2f}%)")

        print(f"\n{Colors.MAGENTA}{'='*60}{Colors.RESET}")


def main():
    """Main function"""
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'Fin-Hub Data Validation & Analysis':^60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}")

    # Validation
    validator = DataValidator()
    validator.validate_stock_data()
    validator.validate_crypto_data()
    validator.validate_gekko_data()
    validator.print_summary()

    # Analysis
    analyzer = DataAnalyzer()
    analyzer.analyze_stock_data()
    analyzer.analyze_crypto_data()
    analyzer.print_analysis()

    # Save report
    report_file = PROJECT_ROOT / "data" / "validation_report.json"
    report = {
        "timestamp": datetime.now().isoformat(),
        "validation": validator.results,
        "analysis": analyzer.analysis
    }

    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\n{Colors.GREEN}[OK] Report saved to: {report_file}{Colors.RESET}")

    # Exit code based on errors
    total_errors = sum(r['errors'] for r in validator.results.values())
    if total_errors > 0:
        print(f"\n{Colors.RED}[WARN] {total_errors} errors found{Colors.RESET}")
        sys.exit(1)
    else:
        print(f"\n{Colors.GREEN}[OK] All data validated successfully!{Colors.RESET}")
        sys.exit(0)


if __name__ == "__main__":
    main()
