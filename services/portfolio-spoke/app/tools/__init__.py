"""
Portfolio Spoke Tools

8 MCP tools for quantitative portfolio management:
1. portfolio_optimizer - Portfolio optimization (Mean-Variance, HRP, Black-Litterman, Risk Parity) ✅
2. portfolio_rebalancer - Generate rebalancing trades ✅
3. performance_analyzer - Performance metrics and attribution ✅
4. backtester - Strategy backtesting ✅
5. factor_analyzer - Factor exposure analysis ✅
6. asset_allocator - Asset allocation (Strategic, Tactical) ✅
7. tax_optimizer - Tax loss harvesting ✅
8. portfolio_dashboard - Comprehensive dashboard ✅
"""

from .portfolio_optimizer import portfolio_optimizer
from .portfolio_rebalancer import portfolio_rebalancer
from .performance_analyzer import performance_analyzer
from .backtester import backtester
from .factor_analyzer import factor_analyzer
from .asset_allocator import asset_allocator
from .tax_optimizer import tax_optimizer
from .portfolio_dashboard import portfolio_dashboard

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
