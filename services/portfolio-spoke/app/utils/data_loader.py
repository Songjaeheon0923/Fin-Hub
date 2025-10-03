"""
Data Loader - Load S&P 500 stock data for portfolio analysis

Provides functions to load historical price data from local CSV files
and calculate returns for portfolio optimization.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Path to S&P 500 data directory
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "stock-data"


def load_stock_prices(
    tickers: List[str],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    column: str = "Close"
) -> pd.DataFrame:
    """
    Load historical stock prices from local CSV files.

    Args:
        tickers: List of stock symbols (e.g., ['AAPL', 'MSFT'])
        start_date: Start date in 'YYYY-MM-DD' format (default: 1 year ago)
        end_date: End date in 'YYYY-MM-DD' format (default: today)
        column: Price column to extract (default: 'Close')

    Returns:
        DataFrame with dates as index and tickers as columns

    Example:
        >>> prices = load_stock_prices(['AAPL', 'MSFT'], '2024-01-01', '2024-12-31')
        >>> print(prices.head())
                    AAPL    MSFT
        2024-01-01  185.23  378.91
        2024-01-02  186.45  380.12
    """
    if not start_date:
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")

    price_data = {}
    missing_tickers = []

    for ticker in tickers:
        csv_path = DATA_DIR / f"{ticker}.csv"

        if not csv_path.exists():
            logger.warning(f"CSV file not found for {ticker}: {csv_path}")
            missing_tickers.append(ticker)
            continue

        try:
            # Read CSV file
            df = pd.read_csv(csv_path)

            # Handle various date column names
            date_col = None
            for col_name in ['Date', 'date', 'timestamp', 'Timestamp']:
                if col_name in df.columns:
                    date_col = col_name
                    break

            if date_col is None:
                logger.error(f"No date column found in {ticker}.csv")
                missing_tickers.append(ticker)
                continue

            # Convert to datetime
            df[date_col] = pd.to_datetime(df[date_col], utc=True)
            df = df.set_index(date_col)

            # Filter date range (convert dates to datetime for comparison)
            start_dt = pd.to_datetime(start_date, utc=True)
            end_dt = pd.to_datetime(end_date, utc=True)
            df = df.loc[start_dt:end_dt]

            # Extract price column
            if column not in df.columns:
                logger.warning(f"Column '{column}' not found for {ticker}, trying alternatives...")
                # Try alternative column names
                if 'close' in df.columns:
                    column = 'close'
                elif 'Adj Close' in df.columns:
                    column = 'Adj Close'
                else:
                    logger.error(f"No price column found for {ticker}")
                    missing_tickers.append(ticker)
                    continue

            price_data[ticker] = df[column]

        except Exception as e:
            logger.error(f"Error loading {ticker}: {str(e)}")
            missing_tickers.append(ticker)

    if missing_tickers:
        logger.warning(f"Missing data for: {', '.join(missing_tickers)}")

    if not price_data:
        raise ValueError("No valid stock data loaded. Check ticker symbols and CSV files.")

    # Combine into single DataFrame
    prices_df = pd.DataFrame(price_data)

    # Forward fill missing values (holidays, etc.)
    prices_df = prices_df.ffill().dropna()

    logger.info(f"Loaded {len(prices_df)} days of data for {len(prices_df.columns)} stocks")

    return prices_df


def calculate_returns(
    prices: pd.DataFrame,
    method: str = "log"
) -> pd.DataFrame:
    """
    Calculate returns from price data.

    Args:
        prices: DataFrame of prices (dates x tickers)
        method: 'log' for log returns, 'simple' for arithmetic returns

    Returns:
        DataFrame of returns (same shape as input)
    """
    if method == "log":
        returns = np.log(prices / prices.shift(1))
    elif method == "simple":
        returns = prices.pct_change()
    else:
        raise ValueError(f"Unknown method: {method}. Use 'log' or 'simple'.")

    return returns.dropna()


def get_covariance_matrix(
    returns: pd.DataFrame,
    method: str = "sample"
) -> pd.DataFrame:
    """
    Calculate covariance matrix from returns.

    Args:
        returns: DataFrame of returns
        method: 'sample', 'shrunk', or 'semicovariance'

    Returns:
        Covariance matrix (tickers x tickers)
    """
    if method == "sample":
        return returns.cov()
    elif method == "shrunk":
        # Ledoit-Wolf shrinkage
        from sklearn.covariance import LedoitWolf
        lw = LedoitWolf()
        cov = lw.fit(returns.dropna()).covariance_
        return pd.DataFrame(cov, index=returns.columns, columns=returns.columns)
    elif method == "semicovariance":
        # Downside covariance (only negative returns)
        negative_returns = returns.copy()
        negative_returns[negative_returns > 0] = 0
        return negative_returns.cov()
    else:
        raise ValueError(f"Unknown method: {method}")


def get_available_tickers() -> List[str]:
    """
    Get list of all available stock tickers from CSV files.

    Returns:
        List of ticker symbols
    """
    if not DATA_DIR.exists():
        logger.error(f"Data directory not found: {DATA_DIR}")
        return []

    csv_files = list(DATA_DIR.glob("*.csv"))

    # Filter out metadata files
    tickers = [
        f.stem for f in csv_files
        if f.stem not in ['_metadata', 'sp500_tickers']
    ]

    return sorted(tickers)


def validate_tickers(tickers: List[str]) -> Tuple[List[str], List[str]]:
    """
    Validate that tickers have corresponding CSV files.

    Args:
        tickers: List of ticker symbols to validate

    Returns:
        Tuple of (valid_tickers, invalid_tickers)
    """
    available = set(get_available_tickers())
    valid = [t for t in tickers if t in available]
    invalid = [t for t in tickers if t not in available]

    return valid, invalid


def get_price_summary(tickers: List[str]) -> Dict[str, Dict]:
    """
    Get summary statistics for stock prices.

    Args:
        tickers: List of ticker symbols

    Returns:
        Dictionary with summary stats for each ticker
    """
    prices = load_stock_prices(tickers)
    returns = calculate_returns(prices)

    summary = {}
    for ticker in tickers:
        if ticker not in prices.columns:
            continue

        price_series = prices[ticker]
        return_series = returns[ticker]

        summary[ticker] = {
            "current_price": float(price_series.iloc[-1]),
            "min_price": float(price_series.min()),
            "max_price": float(price_series.max()),
            "mean_return": float(return_series.mean()),
            "volatility": float(return_series.std()),
            "total_return": float((price_series.iloc[-1] / price_series.iloc[0]) - 1),
            "data_points": len(price_series)
        }

    return summary


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Test: Load AAPL and MSFT prices
    tickers = ["AAPL", "MSFT", "GOOGL"]
    print(f"\nLoading data for: {tickers}")

    prices = load_stock_prices(tickers, start_date="2024-01-01")
    print(f"\nPrices shape: {prices.shape}")
    print(prices.head())

    returns = calculate_returns(prices)
    print(f"\nReturns shape: {returns.shape}")
    print(returns.head())

    cov = get_covariance_matrix(returns)
    print(f"\nCovariance matrix:\n{cov}")

    summary = get_price_summary(tickers)
    print(f"\nSummary:\n{summary}")

    print(f"\nTotal available tickers: {len(get_available_tickers())}")
