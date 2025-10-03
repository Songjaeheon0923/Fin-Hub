"""
Portfolio Math - Core portfolio calculations and utilities

Provides functions for calculating portfolio metrics, risk measures,
and optimization utilities.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from scipy import stats
import logging

logger = logging.getLogger(__name__)


def portfolio_return(weights: np.ndarray, mean_returns: np.ndarray) -> float:
    """
    Calculate expected portfolio return.

    Args:
        weights: Array of portfolio weights (must sum to 1)
        mean_returns: Array of expected returns for each asset

    Returns:
        Expected portfolio return
    """
    return np.dot(weights, mean_returns)


def portfolio_volatility(weights: np.ndarray, cov_matrix: np.ndarray) -> float:
    """
    Calculate portfolio volatility (standard deviation).

    Args:
        weights: Array of portfolio weights
        cov_matrix: Covariance matrix of asset returns

    Returns:
        Portfolio volatility (annualized if cov_matrix is annualized)
    """
    return np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))


def sharpe_ratio(
    portfolio_return: float,
    portfolio_volatility: float,
    risk_free_rate: float = 0.03
) -> float:
    """
    Calculate Sharpe ratio.

    Args:
        portfolio_return: Expected portfolio return
        portfolio_volatility: Portfolio standard deviation
        risk_free_rate: Risk-free rate (default: 3%)

    Returns:
        Sharpe ratio
    """
    if portfolio_volatility == 0:
        return 0.0
    return (portfolio_return - risk_free_rate) / portfolio_volatility


def sortino_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.03,
    target_return: float = 0.0
) -> float:
    """
    Calculate Sortino ratio (uses downside deviation instead of total volatility).

    Args:
        returns: Time series of portfolio returns
        risk_free_rate: Risk-free rate
        target_return: Minimum acceptable return (default: 0)

    Returns:
        Sortino ratio
    """
    excess_return = returns.mean() - risk_free_rate / 252  # Daily risk-free rate

    # Downside deviation (only negative returns below target)
    downside_returns = returns[returns < target_return]
    if len(downside_returns) == 0:
        return np.inf

    downside_std = downside_returns.std()

    if downside_std == 0:
        return np.inf

    # Annualize
    sortino = (excess_return * np.sqrt(252)) / (downside_std * np.sqrt(252))
    return sortino


def max_drawdown(returns: pd.Series) -> float:
    """
    Calculate maximum drawdown.

    Args:
        returns: Time series of returns

    Returns:
        Maximum drawdown (as positive percentage)
    """
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.cummax()
    drawdown = (cumulative - running_max) / running_max
    return abs(drawdown.min())


def calmar_ratio(returns: pd.Series) -> float:
    """
    Calculate Calmar ratio (annualized return / max drawdown).

    Args:
        returns: Time series of returns

    Returns:
        Calmar ratio
    """
    mdd = max_drawdown(returns)
    if mdd == 0:
        return np.inf

    annualized_return = (1 + returns.mean()) ** 252 - 1
    return annualized_return / mdd


def calculate_beta(
    asset_returns: pd.Series,
    market_returns: pd.Series
) -> float:
    """
    Calculate beta (systematic risk relative to market).

    Args:
        asset_returns: Time series of asset returns
        market_returns: Time series of market (benchmark) returns

    Returns:
        Beta coefficient
    """
    # Align the two series
    df = pd.DataFrame({
        'asset': asset_returns,
        'market': market_returns
    }).dropna()

    if len(df) < 2:
        return 1.0  # Default to market beta

    covariance = df['asset'].cov(df['market'])
    market_variance = df['market'].var()

    if market_variance == 0:
        return 1.0

    return covariance / market_variance


def calculate_alpha(
    asset_returns: pd.Series,
    market_returns: pd.Series,
    risk_free_rate: float = 0.03
) -> float:
    """
    Calculate alpha (excess return over CAPM prediction).

    Args:
        asset_returns: Time series of asset returns
        market_returns: Time series of market returns
        risk_free_rate: Risk-free rate (annualized)

    Returns:
        Annualized alpha
    """
    beta = calculate_beta(asset_returns, market_returns)

    # Annualize returns
    asset_return_annual = (1 + asset_returns.mean()) ** 252 - 1
    market_return_annual = (1 + market_returns.mean()) ** 252 - 1

    # CAPM expected return
    expected_return = risk_free_rate + beta * (market_return_annual - risk_free_rate)

    # Alpha = actual return - expected return
    return asset_return_annual - expected_return


def information_ratio(
    portfolio_returns: pd.Series,
    benchmark_returns: pd.Series
) -> float:
    """
    Calculate information ratio (excess return / tracking error).

    Args:
        portfolio_returns: Time series of portfolio returns
        benchmark_returns: Time series of benchmark returns

    Returns:
        Information ratio
    """
    # Align series
    df = pd.DataFrame({
        'portfolio': portfolio_returns,
        'benchmark': benchmark_returns
    }).dropna()

    if len(df) < 2:
        return 0.0

    excess_returns = df['portfolio'] - df['benchmark']
    tracking_error = excess_returns.std()

    if tracking_error == 0:
        return 0.0

    # Annualize
    annualized_excess = excess_returns.mean() * np.sqrt(252)
    annualized_te = tracking_error * np.sqrt(252)

    return annualized_excess / annualized_te


def diversification_ratio(
    weights: np.ndarray,
    volatilities: np.ndarray,
    cov_matrix: np.ndarray
) -> float:
    """
    Calculate diversification ratio.

    DR = (weighted average volatility) / (portfolio volatility)

    Higher ratio = better diversification

    Args:
        weights: Portfolio weights
        volatilities: Individual asset volatilities
        cov_matrix: Covariance matrix

    Returns:
        Diversification ratio (>1 means diversification benefit)
    """
    weighted_avg_vol = np.dot(weights, volatilities)
    portfolio_vol = portfolio_volatility(weights, cov_matrix)

    if portfolio_vol == 0:
        return 1.0

    return weighted_avg_vol / portfolio_vol


def herfindahl_index(weights: np.ndarray) -> float:
    """
    Calculate Herfindahl-Hirschman Index for concentration risk.

    HHI = sum of squared weights
    0.0 = perfectly diversified, 1.0 = concentrated in one asset

    Args:
        weights: Portfolio weights

    Returns:
        HHI (0-1)
    """
    return np.sum(weights ** 2)


def effective_number_of_assets(weights: np.ndarray) -> float:
    """
    Calculate effective number of assets (ENB).

    ENB = 1 / HHI

    Args:
        weights: Portfolio weights

    Returns:
        Effective number of assets
    """
    hhi = herfindahl_index(weights)
    if hhi == 0:
        return 0.0
    return 1.0 / hhi


def annualize_return(daily_return: float, periods: int = 252) -> float:
    """
    Annualize a daily return.

    Args:
        daily_return: Average daily return
        periods: Number of periods per year (default: 252 trading days)

    Returns:
        Annualized return
    """
    return (1 + daily_return) ** periods - 1


def annualize_volatility(daily_vol: float, periods: int = 252) -> float:
    """
    Annualize daily volatility.

    Args:
        daily_vol: Daily volatility (standard deviation)
        periods: Number of periods per year (default: 252 trading days)

    Returns:
        Annualized volatility
    """
    return daily_vol * np.sqrt(periods)


def calculate_var(
    returns: pd.Series,
    confidence_level: float = 0.95,
    method: str = "historical"
) -> float:
    """
    Calculate Value at Risk (VaR).

    Args:
        returns: Time series of returns
        confidence_level: Confidence level (default: 95%)
        method: 'historical' or 'parametric'

    Returns:
        VaR (as positive percentage, e.g., 0.05 = 5% loss)
    """
    if method == "historical":
        return abs(returns.quantile(1 - confidence_level))
    elif method == "parametric":
        # Assume normal distribution
        mean = returns.mean()
        std = returns.std()
        z_score = stats.norm.ppf(1 - confidence_level)
        return abs(mean + z_score * std)
    else:
        raise ValueError(f"Unknown VaR method: {method}")


def calculate_cvar(
    returns: pd.Series,
    confidence_level: float = 0.95
) -> float:
    """
    Calculate Conditional Value at Risk (CVaR / Expected Shortfall).

    CVaR = average loss beyond VaR threshold

    Args:
        returns: Time series of returns
        confidence_level: Confidence level (default: 95%)

    Returns:
        CVaR (as positive percentage)
    """
    var = calculate_var(returns, confidence_level, method="historical")
    # Get returns worse than VaR
    tail_returns = returns[returns <= -var]

    if len(tail_returns) == 0:
        return var

    return abs(tail_returns.mean())


def weights_sum_to_one(weights: np.ndarray, tolerance: float = 1e-4) -> bool:
    """
    Check if weights sum to 1 (within tolerance).

    Args:
        weights: Portfolio weights
        tolerance: Acceptable deviation from 1.0

    Returns:
        True if valid
    """
    return abs(np.sum(weights) - 1.0) < tolerance


def normalize_weights(weights: np.ndarray) -> np.ndarray:
    """
    Normalize weights to sum to 1.

    Args:
        weights: Portfolio weights

    Returns:
        Normalized weights
    """
    total = np.sum(weights)
    if total == 0:
        return np.ones_like(weights) / len(weights)  # Equal weights
    return weights / total


def convert_to_dict(weights: np.ndarray, tickers: List[str]) -> Dict[str, float]:
    """
    Convert weight array to dictionary.

    Args:
        weights: Array of weights
        tickers: List of ticker symbols

    Returns:
        Dictionary mapping ticker -> weight
    """
    return {ticker: float(weight) for ticker, weight in zip(tickers, weights)}


# Example usage
if __name__ == "__main__":
    # Test with sample data
    np.random.seed(42)

    # 3 assets
    mean_returns = np.array([0.12, 0.10, 0.08])  # 12%, 10%, 8% annual
    cov_matrix = np.array([
        [0.04, 0.01, 0.005],
        [0.01, 0.03, 0.008],
        [0.005, 0.008, 0.02]
    ])
    weights = np.array([0.4, 0.4, 0.2])

    print("Portfolio Metrics Test:")
    print(f"Expected Return: {portfolio_return(weights, mean_returns):.2%}")
    print(f"Volatility: {portfolio_volatility(weights, cov_matrix):.2%}")
    print(f"Sharpe Ratio: {sharpe_ratio(0.12, 0.20, 0.03):.2f}")

    print(f"\nDiversification:")
    print(f"HHI: {herfindahl_index(weights):.4f}")
    print(f"Effective # Assets: {effective_number_of_assets(weights):.2f}")

    # Test with sample returns
    returns = pd.Series(np.random.normal(0.0005, 0.01, 252))  # Daily returns
    print(f"\nRisk Metrics:")
    print(f"Max Drawdown: {max_drawdown(returns):.2%}")
    print(f"VaR (95%): {calculate_var(returns):.2%}")
    print(f"CVaR (95%): {calculate_cvar(returns):.2%}")
