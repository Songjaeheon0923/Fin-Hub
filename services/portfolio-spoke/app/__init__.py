"""
Portfolio Spoke - Quantitative Portfolio Management

Provides 8 MCP tools for portfolio optimization, rebalancing, performance analysis,
backtesting, factor analysis, asset allocation, tax optimization, and dashboard.
"""

__version__ = "1.0.0"
__author__ = "Fin-Hub Development Team"

from app.tools import (
    portfolio_optimizer,
    portfolio_rebalancer,
    performance_analyzer,
    backtester,
    factor_analyzer,
    asset_allocator,
    tax_optimizer,
    portfolio_dashboard
)

__all__ = [
    "portfolio_optimizer",
    "portfolio_rebalancer",
    "performance_analyzer",
    "backtester",
    "factor_analyzer",
    "asset_allocator",
    "tax_optimizer",
    "portfolio_dashboard"
]
