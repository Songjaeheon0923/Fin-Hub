#!/usr/bin/env python3
"""
S&P 500 Full Dataset Download Script for Fin-Hub
Downloads complete historical data for all 500 S&P 500 stocks
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Tuple
import pandas as pd
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuration
DATA_DIR = Path(__file__).parent.parent / "data" / "stock-data"
METADATA_FILE = DATA_DIR / "_metadata.json"
PERIOD = "5y"  # 5 years of historical data
INTERVAL = "1d"  # Daily data
MAX_WORKERS = 10  # Parallel download threads

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def get_hardcoded_sp500_list() -> List[str]:
    """
    Hardcoded list of top 100 S&P 500 stocks as fallback
    Returns: List of ticker symbols
    """
    return [
        # Technology (Magnificent 7 + major tech)
        'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'NVDA', 'META', 'TSLA',
        'AVGO', 'ORCL', 'ADBE', 'CRM', 'CSCO', 'ACN', 'AMD', 'INTC', 'IBM', 'QCOM', 'TXN', 'INTU',

        # Healthcare
        'UNH', 'JNJ', 'LLY', 'ABBV', 'MRK', 'TMO', 'ABT', 'DHR', 'BMY', 'AMGN',
        'GILD', 'CVS', 'CI', 'PFE', 'ISRG', 'REGN', 'VRTX', 'MCK', 'ELV', 'HCA',

        # Finance
        'BRK-B', 'JPM', 'V', 'MA', 'BAC', 'WFC', 'GS', 'MS', 'AXP', 'BLK',
        'SPGI', 'C', 'CB', 'MMC', 'PGR', 'AON', 'CME', 'ICE', 'USB', 'PNC',

        # Consumer
        'WMT', 'HD', 'COST', 'MCD', 'NKE', 'SBUX', 'TGT', 'LOW', 'TJX', 'DG',
        'ROST', 'YUM', 'ORLY', 'AZO', 'CMG', 'ULTA', 'EBAY', 'BKNG', 'MAR',

        # Industrial & Energy
        'XOM', 'CVX', 'LIN', 'CAT', 'GE', 'RTX', 'BA', 'UNP', 'HON', 'UPS',
        'DE', 'ADP', 'LMT', 'MMM', 'GD', 'NOC', 'FDX', 'NSC', 'WM', 'ETN',

        # Communication & Media
        'NFLX', 'DIS', 'CMCSA', 'T', 'VZ', 'TMUS', 'CHTR',

        # Consumer Staples
        'PG', 'KO', 'PEP', 'PM', 'MDLZ', 'MO', 'CL', 'KMB', 'GIS', 'K'
    ]


def get_sp500_tickers() -> List[str]:
    """
    Get list of S&P 500 tickers from Wikipedia
    Returns: List of ticker symbols
    """
    try:
        print(f"{Colors.BLUE}[INFO] Fetching S&P 500 ticker list from Wikipedia...{Colors.RESET}")

        # Read S&P 500 list from Wikipedia with proper headers
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"

        # Add headers to avoid 403 error
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        tables = pd.read_html(url, storage_options={'User-Agent': headers['User-Agent']})
        sp500_table = tables[0]

        tickers = sp500_table['Symbol'].tolist()

        # Clean up ticker symbols (some have special characters)
        tickers = [ticker.replace('.', '-') for ticker in tickers]

        print(f"{Colors.GREEN}[OK] Found {len(tickers)} S&P 500 companies{Colors.RESET}")

        # Save ticker list for reference
        ticker_file = DATA_DIR / "sp500_tickers.json"
        with open(ticker_file, 'w') as f:
            json.dump({
                "tickers": tickers,
                "count": len(tickers),
                "date_fetched": datetime.now().isoformat()
            }, f, indent=2)

        return tickers

    except Exception as e:
        print(f"{Colors.RED}[ERROR] Failed to fetch S&P 500 list: {e}{Colors.RESET}")
        print(f"{Colors.YELLOW}[WARN] Falling back to hardcoded list...{Colors.RESET}")

        # Fallback to cached list if available
        ticker_file = DATA_DIR / "sp500_tickers.json"
        if ticker_file.exists():
            with open(ticker_file, 'r') as f:
                data = json.load(f)
                return data['tickers']

        # Ultimate fallback: hardcoded list of major S&P 500 stocks
        print(f"{Colors.YELLOW}[WARN] Using hardcoded list of top 100 S&P 500 stocks{Colors.RESET}")
        return get_hardcoded_sp500_list()


def download_single_stock(ticker: str, period: str = PERIOD, interval: str = INTERVAL) -> Tuple[str, bool, str]:
    """
    Download data for a single stock
    Returns: (ticker, success, error_message)
    """
    try:
        # Download data
        stock = yf.Ticker(ticker)
        df = stock.history(period=period, interval=interval)

        if df.empty:
            return (ticker, False, "No data returned")

        # Save to CSV
        output_file = DATA_DIR / f"{ticker}.csv"
        df.to_csv(output_file)

        return (ticker, True, f"Downloaded {len(df)} records")

    except Exception as e:
        return (ticker, False, str(e))


def download_stocks_parallel(tickers: List[str], max_workers: int = MAX_WORKERS) -> Dict:
    """
    Download multiple stocks in parallel
    Returns: Dictionary with results
    """
    results = {
        "successful": [],
        "failed": [],
        "total": len(tickers),
        "start_time": datetime.now().isoformat()
    }

    print(f"\n{Colors.BOLD}{Colors.BLUE}Starting parallel download with {max_workers} workers...{Colors.RESET}")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all download tasks
        future_to_ticker = {
            executor.submit(download_single_stock, ticker): ticker
            for ticker in tickers
        }

        # Process completed downloads
        completed = 0
        for future in as_completed(future_to_ticker):
            ticker, success, message = future.result()
            completed += 1

            if success:
                results["successful"].append({
                    "ticker": ticker,
                    "message": message
                })
                print(f"{Colors.GREEN}[{completed}/{len(tickers)}] {ticker}: {message}{Colors.RESET}")
            else:
                results["failed"].append({
                    "ticker": ticker,
                    "error": message
                })
                print(f"{Colors.RED}[{completed}/{len(tickers)}] {ticker}: FAILED - {message}{Colors.RESET}")

            # Rate limiting (be nice to Yahoo Finance)
            if completed % 50 == 0:
                print(f"{Colors.YELLOW}[INFO] Pausing for rate limiting...{Colors.RESET}")
                time.sleep(5)

    results["end_time"] = datetime.now().isoformat()

    return results


def update_metadata(results: Dict):
    """
    Update metadata file with download results
    """
    metadata = {
        "last_update": datetime.now().isoformat(),
        "period": PERIOD,
        "interval": INTERVAL,
        "total_stocks": results["total"],
        "successful_downloads": len(results["successful"]),
        "failed_downloads": len(results["failed"]),
        "success_rate": f"{len(results['successful']) / results['total'] * 100:.2f}%",
        "successful_tickers": [item["ticker"] for item in results["successful"]],
        "failed_tickers": [item["ticker"] for item in results["failed"]],
        "download_start": results["start_time"],
        "download_end": results["end_time"]
    }

    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"\n{Colors.BLUE}[INFO] Metadata saved to {METADATA_FILE}{Colors.RESET}")


def print_summary(results: Dict):
    """
    Print download summary
    """
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'Download Summary':^60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")

    success_count = len(results["successful"])
    fail_count = len(results["failed"])
    total = results["total"]

    print(f"{Colors.BOLD}Results:{Colors.RESET}")
    print(f"  {Colors.GREEN}[OK] Successful: {success_count}/{total} ({success_count/total*100:.1f}%){Colors.RESET}")

    if fail_count > 0:
        print(f"  {Colors.RED}[ERROR] Failed: {fail_count}/{total} ({fail_count/total*100:.1f}%){Colors.RESET}")
        print(f"\n{Colors.YELLOW}Failed tickers:{Colors.RESET}")
        for item in results["failed"][:10]:  # Show first 10 failures
            print(f"    - {item['ticker']}: {item['error']}")
        if fail_count > 10:
            print(f"    ... and {fail_count - 10} more")

    # Calculate total data size
    total_size = sum(
        (DATA_DIR / f"{item['ticker']}.csv").stat().st_size
        for item in results["successful"]
        if (DATA_DIR / f"{item['ticker']}.csv").exists()
    )

    print(f"\n{Colors.BOLD}Storage:{Colors.RESET}")
    print(f"  Total size: {total_size / 1024 / 1024:.2f} MB")
    print(f"  Location: {DATA_DIR}")

    # Time taken
    start = datetime.fromisoformat(results["start_time"])
    end = datetime.fromisoformat(results["end_time"])
    duration = (end - start).total_seconds()

    print(f"\n{Colors.BOLD}Performance:{Colors.RESET}")
    print(f"  Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
    print(f"  Average: {duration/total:.2f} seconds per stock")

    print(f"\n{Colors.GREEN}{'='*60}{Colors.RESET}")


def main():
    """
    Main function
    """
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'S&P 500 Full Dataset Downloader':^60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")

    # Create data directory
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Check for --yes flag
    auto_yes = '--yes' in sys.argv or '-y' in sys.argv

    # Get S&P 500 tickers
    try:
        tickers = get_sp500_tickers()
    except Exception as e:
        print(f"{Colors.RED}[ERROR] Failed to get ticker list: {e}{Colors.RESET}")
        sys.exit(1)

    # Show info
    print(f"\n{Colors.YELLOW}[INFO] Will download {len(tickers)} stocks (~{len(tickers) * 6} MB total){Colors.RESET}")
    print(f"{Colors.YELLOW}[INFO] Period: {PERIOD}, Interval: {INTERVAL}{Colors.RESET}")

    # Ask for confirmation unless --yes flag is used
    if not auto_yes:
        try:
            response = input(f"\n{Colors.BOLD}Continue? (y/n): {Colors.RESET}")
            if response.lower() != 'y':
                print(f"{Colors.YELLOW}[INFO] Download cancelled{Colors.RESET}")
                sys.exit(0)
        except (EOFError, KeyboardInterrupt):
            print(f"\n{Colors.YELLOW}[INFO] Download cancelled{Colors.RESET}")
            sys.exit(0)
    else:
        print(f"{Colors.GREEN}[INFO] Auto-confirming (--yes flag detected){Colors.RESET}")

    # Download stocks
    results = download_stocks_parallel(tickers)

    # Update metadata
    update_metadata(results)

    # Print summary
    print_summary(results)

    # Exit code
    if len(results["failed"]) > 0:
        print(f"\n{Colors.YELLOW}[WARN] Some downloads failed. Check the log above.{Colors.RESET}")
        sys.exit(1)
    else:
        print(f"\n{Colors.GREEN}[OK] All downloads completed successfully!{Colors.RESET}")
        sys.exit(0)


if __name__ == "__main__":
    main()
