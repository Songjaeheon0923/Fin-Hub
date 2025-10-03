# 📊 Portfolio Spoke - Design Specification

**Version**: 1.0
**Date**: 2025-10-04
**Status**: Design Phase
**Dependencies**: Market Spoke (13 tools), Risk Spoke (8 tools)

---

## 🎯 Overview

Portfolio Spoke provides quantitative portfolio management capabilities including optimization, rebalancing, performance analysis, backtesting, and tax optimization. Integrates with Market Spoke for price data and Risk Spoke for risk metrics.

**Key Differentiators**:
- MCP protocol integration (unique in market)
- Quantitative focus over UI
- Tax optimization (2025 priority)
- Factor investing capabilities
- Seamless Market + Risk Spoke integration

---

## 🏗️ Architecture

```
services/portfolio-spoke/
├── app/
│   ├── __init__.py
│   ├── main.py                      # FastAPI app (optional REST API)
│   ├── tools/                       # 8 MCP tools
│   │   ├── __init__.py
│   │   ├── portfolio_optimizer.py   # Mean-Variance, HRP, Black-Litterman
│   │   ├── portfolio_rebalancer.py  # Trade generation, cost optimization
│   │   ├── performance_analyzer.py  # Metrics, attribution, benchmarking
│   │   ├── backtester.py            # Strategy simulation
│   │   ├── factor_analyzer.py       # Factor exposure, attribution
│   │   ├── asset_allocator.py       # Strategic/tactical allocation
│   │   ├── tax_optimizer.py         # Tax loss harvesting
│   │   └── portfolio_dashboard.py   # Comprehensive summary
│   ├── models/                      # Data models
│   │   ├── portfolio.py
│   │   ├── position.py
│   │   └── transaction.py
│   └── utils/
│       ├── portfolio_math.py        # Core calculations
│       └── data_loader.py           # Load S&P 500 data
├── mcp_server.py                    # MCP server (JSON-RPC)
├── start_mcp_server.py              # Launcher
├── requirements.txt
└── tests/
    └── test_portfolio_tools.py
```

---

## 🔧 Tool Specifications

### 1. Portfolio Optimizer (`portfolio_optimizer`)

**Purpose**: Generate optimal portfolio weights using various strategies.

**Input Parameters**:
```python
{
    "tickers": ["AAPL", "MSFT", "GOOGL"],     # 2-50 stocks
    "method": "mean_variance",                 # mean_variance | hrp | black_litterman | risk_parity | max_sharpe | min_volatility
    "objective": "max_sharpe",                 # max_sharpe | min_volatility | efficient_return | efficient_risk
    "target_return": 0.15,                     # Optional: for efficient_return
    "target_risk": 0.20,                       # Optional: for efficient_risk
    "constraints": {                           # Optional
        "max_weight": 0.30,                    # Max 30% per stock
        "min_weight": 0.02,                    # Min 2% per stock
        "sector_constraints": {...}
    },
    "risk_free_rate": 0.03,                    # Default: 3%
    "views": {...}                             # For Black-Litterman only
}
```

**Output**:
```python
{
    "weights": {"AAPL": 0.35, "MSFT": 0.40, "GOOGL": 0.25},
    "expected_return": 0.18,
    "expected_risk": 0.22,
    "sharpe_ratio": 0.68,
    "method_used": "mean_variance",
    "efficient_frontier": [...],               # Points for plotting
    "interpretation": "Portfolio optimized for maximum Sharpe ratio..."
}
```

**Implementation**:
- **Library**: PyPortfolioOpt (primary), Riskfolio-Lib (advanced)
- **Data Source**: Market Spoke → unified_market_data (historical prices)
- **Period**: 252 trading days (1 year)
- **Optimization Methods**:
  - Mean-Variance: Markowitz (1952)
  - HRP: Hierarchical Risk Parity (de Prado)
  - Black-Litterman: Bayesian views incorporation
  - Risk Parity: Equal risk contribution
  - Max Sharpe: Maximize risk-adjusted return
  - Min Volatility: Minimize portfolio variance

---

### 2. Portfolio Rebalancer (`portfolio_rebalancer`)

**Purpose**: Generate trade actions to rebalance portfolio to target weights.

**Input Parameters**:
```python
{
    "current_positions": {                     # Current holdings
        "AAPL": {"shares": 100, "value": 18500}
    },
    "target_weights": {                        # From optimizer
        "AAPL": 0.30, "MSFT": 0.40, "GOOGL": 0.30
    },
    "total_value": 100000,                     # Portfolio value
    "cash_available": 5000,                    # Cash for new purchases
    "strategy": "threshold",                   # threshold | periodic | tax_aware
    "threshold": 0.05,                         # 5% drift triggers rebalance
    "minimize_trades": true,                   # Reduce transaction count
    "constraints": {
        "max_turnover": 0.20,                  # Max 20% turnover
        "no_sell_list": ["AAPL"]               # Hold positions
    }
}
```

**Output**:
```python
{
    "trades": [
        {"ticker": "AAPL", "action": "sell", "shares": 20, "value": 3700, "reason": "overweight"},
        {"ticker": "MSFT", "action": "buy", "shares": 80, "value": 32000, "reason": "underweight"}
    ],
    "total_cost": 150,                         # Transaction costs
    "turnover": 0.18,                          # 18% portfolio turnover
    "drift_before": {"AAPL": 0.08, "MSFT": -0.10},
    "drift_after": {"AAPL": 0.02, "MSFT": -0.01},
    "interpretation": "Rebalancing requires 2 trades with $150 cost..."
}
```

**Implementation**:
- **Library**: Custom (simple optimization)
- **Algorithm**: Minimize |target - current| with constraints
- **Cost Model**: $0.01 per share (configurable)
- **Tax Awareness**: Integrate with tax_optimizer for loss harvesting

---

### 3. Performance Analyzer (`performance_analyzer`)

**Purpose**: Calculate portfolio performance metrics and attribution analysis.

**Input Parameters**:
```python
{
    "positions": {                             # Holdings
        "AAPL": {"shares": 100, "avg_cost": 150}
    },
    "transactions": [...],                     # Historical trades
    "benchmark": "SPY",                        # S&P 500 ETF
    "start_date": "2024-01-01",
    "end_date": "2025-10-04",
    "risk_free_rate": 0.03
}
```

**Output**:
```python
{
    "returns": {
        "total_return": 0.25,                  # 25%
        "annualized_return": 0.18,
        "ytd_return": 0.12,
        "mtd_return": 0.03
    },
    "risk_metrics": {
        "volatility": 0.22,
        "sharpe_ratio": 0.68,
        "sortino_ratio": 0.95,
        "max_drawdown": -0.15,
        "calmar_ratio": 1.20,
        "beta": 0.85,
        "alpha": 0.03
    },
    "benchmark_comparison": {
        "benchmark_return": 0.20,
        "excess_return": 0.05,                 # Outperformance
        "tracking_error": 0.08,
        "information_ratio": 0.625
    },
    "attribution": {                           # Contribution by holding
        "AAPL": 0.08,
        "MSFT": 0.10,
        "GOOGL": 0.07
    },
    "interpretation": "Portfolio outperformed benchmark by 5% with lower beta..."
}
```

**Implementation**:
- **Library**: PyFolio, custom calculations
- **Data Source**: Market Spoke (price history), Risk Spoke (risk metrics)
- **Benchmark**: Calculate from S&P 500 data

---

### 4. Backtester (`backtester`)

**Purpose**: Simulate portfolio strategies on historical data.

**Input Parameters**:
```python
{
    "strategy": "momentum",                    # momentum | mean_reversion | factor_based | custom
    "universe": "sp500",                       # sp500 | custom
    "custom_tickers": ["AAPL", "MSFT"],        # If custom
    "start_date": "2020-01-01",
    "end_date": "2024-12-31",
    "initial_capital": 100000,
    "rebalance_frequency": "monthly",          # daily | weekly | monthly | quarterly
    "parameters": {                            # Strategy-specific
        "lookback": 60,                        # 60 days for momentum
        "top_n": 20                            # Top 20 stocks
    },
    "transaction_cost": 0.001,                 # 0.1% per trade
    "slippage": 0.0005                         # 0.05% slippage
}
```

**Output**:
```python
{
    "performance": {
        "total_return": 0.85,                  # 85% over period
        "annualized_return": 0.16,
        "sharpe_ratio": 1.25,
        "max_drawdown": -0.22,
        "win_rate": 0.58
    },
    "equity_curve": [...],                     # Daily portfolio values
    "trades": [...],                           # All executed trades
    "monthly_returns": [...],
    "metrics_by_year": {...},
    "benchmark_comparison": {
        "strategy_return": 0.85,
        "buy_hold_return": 0.65,
        "outperformance": 0.20
    },
    "interpretation": "Momentum strategy achieved 16% annualized return..."
}
```

**Implementation**:
- **Library**: VectorBT (high performance), Backtrader (comprehensive)
- **Data**: S&P 500 historical prices (503 stocks, 5 years)
- **Strategies**: Pre-built + custom Python functions

---

### 5. Factor Analyzer (`factor_analyzer`)

**Purpose**: Analyze factor exposures and attribution (Fama-French, custom factors).

**Input Parameters**:
```python
{
    "positions": {"AAPL": 0.30, "MSFT": 0.40},
    "factors": ["market", "size", "value", "momentum", "quality"],
    "start_date": "2024-01-01",
    "end_date": "2025-10-04"
}
```

**Output**:
```python
{
    "factor_exposures": {
        "market": 0.95,                        # Beta
        "size": -0.15,                         # Large cap bias
        "value": -0.08,                        # Growth tilt
        "momentum": 0.25,
        "quality": 0.18
    },
    "factor_returns": {                        # Attribution
        "market": 0.12,
        "size": -0.02,
        "value": -0.01,
        "momentum": 0.04,
        "quality": 0.03,
        "alpha": 0.02                          # Unexplained return
    },
    "r_squared": 0.88,                         # Model fit
    "interpretation": "Portfolio has strong momentum and quality tilt..."
}
```

**Implementation**:
- **Library**: Alphalens (Quantopian), custom regression
- **Data Source**:
  - Fama-French factors (free from Kenneth French website)
  - Custom factors calculated from S&P 500 data
- **Regression**: OLS factor model

---

### 6. Asset Allocator (`asset_allocator`)

**Purpose**: Strategic and tactical asset allocation across asset classes.

**Input Parameters**:
```python
{
    "asset_classes": {                         # Available assets
        "stocks": ["AAPL", "MSFT"],
        "bonds": ["AGG"],                      # Bond ETF
        "crypto": ["BTC", "ETH"],
        "commodities": ["GLD"]                 # Gold ETF
    },
    "strategy": "strategic",                   # strategic | tactical | dynamic
    "risk_profile": "moderate",                # conservative | moderate | aggressive
    "target_allocation": {                     # For strategic
        "stocks": 0.60,
        "bonds": 0.30,
        "crypto": 0.05,
        "commodities": 0.05
    },
    "rebalance_bands": {                       # Tactical bands
        "stocks": 0.10                         # ±10% drift
    }
}
```

**Output**:
```python
{
    "allocation": {
        "stocks": 0.58,
        "bonds": 0.32,
        "crypto": 0.05,
        "commodities": 0.05
    },
    "expected_return": 0.12,
    "expected_risk": 0.15,
    "sharpe_ratio": 0.60,
    "diversification_ratio": 1.35,             # Higher = better diversification
    "interpretation": "Moderate risk portfolio with 60/30 stock/bond allocation..."
}
```

**Implementation**:
- **Library**: Riskfolio-Lib (asset allocation focus)
- **Data**: Market Spoke for all asset classes
- **Strategies**:
  - Strategic: Fixed target weights
  - Tactical: Adjust based on market conditions
  - Dynamic: ML-based (future phase)

---

### 7. Tax Optimizer (`tax_optimizer`)

**Purpose**: Tax loss harvesting and tax-efficient rebalancing.

**Input Parameters**:
```python
{
    "positions": {
        "AAPL": {"shares": 100, "avg_cost": 180, "current_price": 150},  # Loss
        "MSFT": {"shares": 50, "avg_cost": 300, "current_price": 420}   # Gain
    },
    "tax_rate": {
        "short_term": 0.37,                    # < 1 year
        "long_term": 0.20                      # > 1 year
    },
    "harvest_threshold": 1000,                 # Min $1000 loss
    "wash_sale_period": 30                     # 30 days
}
```

**Output**:
```python
{
    "harvest_opportunities": [
        {
            "ticker": "AAPL",
            "shares": 100,
            "realized_loss": -3000,
            "tax_benefit": 1110,               # 37% of loss
            "replacement": "MSFT",             # Similar stock (avoid wash sale)
            "wash_sale_risk": false
        }
    ],
    "total_tax_benefit": 1110,
    "recommendations": [...],
    "interpretation": "Harvesting AAPL loss provides $1,110 tax benefit..."
}
```

**Implementation**:
- **Library**: Custom (tax rules specific)
- **Data**: Position history, transaction dates
- **Rules**:
  - Wash sale: 30-day rule (IRS)
  - Long-term vs short-term gains
  - $3,000 annual loss deduction limit

---

### 8. Portfolio Dashboard (`portfolio_dashboard`)

**Purpose**: Comprehensive portfolio summary and health check.

**Input Parameters**:
```python
{
    "portfolio_id": "default",
    "include_details": true
}
```

**Output**:
```python
{
    "summary": {
        "total_value": 125000,
        "cash": 5000,
        "positions_value": 120000,
        "num_positions": 15,
        "total_return": 0.25,
        "ytd_return": 0.12
    },
    "performance": {
        "sharpe_ratio": 0.85,
        "max_drawdown": -0.15,
        "beta": 0.90,
        "alpha": 0.03
    },
    "risk_metrics": {
        "volatility": 0.20,
        "var_95": 2500,                        # 95% VaR
        "concentration_risk": "medium",
        "sector_exposure": {...}
    },
    "rebalancing_needed": true,
    "drift": {"AAPL": 0.08, "MSFT": -0.05},
    "tax_harvest_opportunities": 2,
    "health_score": 85,                        # 0-100
    "alerts": [
        "AAPL overweight by 8%",
        "2 tax loss harvesting opportunities"
    ],
    "interpretation": "Portfolio is healthy with moderate rebalancing needed..."
}
```

**Implementation**:
- **Library**: Aggregation of all other tools
- **Data**: Calls other portfolio tools internally

---

## 📊 Data Requirements

### Already Available (✅)
- **S&P 500 stocks**: 503 tickers, 5 years daily data (71 MB)
- **Market data**: unified_market_data tool (Market Spoke)
- **Risk metrics**: 8 tools (Risk Spoke)
- **Crypto prices**: CoinGecko API
- **Economic indicators**: FRED API

### Required (🔄)
1. **Fama-French Factors** (FREE)
   - Source: Kenneth French Data Library
   - Frequency: Daily/Monthly
   - Factors: Market, SMB, HML, RMW, CMA, Momentum
   - Download: `pip install pandas_datareader`

2. **ETF Data** (Optional, can use existing stocks)
   - AGG (bonds), SPY (S&P 500), GLD (gold)
   - Workaround: Use large-cap stocks as proxies

3. **Benchmarks** (Can calculate)
   - S&P 500 return: Calculate from 503 stocks
   - Equal-weight index: Average returns

### Not Required
- ❌ Fundamentals: Not needed for portfolio optimization
- ❌ Options data: Not in scope for Phase 1
- ❌ Real-time tick data: Daily OHLCV sufficient

---

## 🛠️ Technology Stack

### Core Libraries
```bash
# Portfolio Optimization
pip install pyportfolioopt==1.5.5          # Most widely used
pip install riskfolio-lib==6.3.0           # Advanced risk management
pip install skfolio==0.4.0                 # Latest 2025 library

# Backtesting
pip install vectorbt==0.26.1               # High performance
pip install backtrader==1.9.78.123         # Comprehensive

# Factor Analysis
pip install alphalens-reloaded==0.4.5      # Factor analysis
pip install pandas-datareader==0.10.0      # Fama-French data

# Performance Analytics
pip install pyfolio-reloaded==0.9.9        # Performance metrics
pip install quantstats==0.0.62             # Risk metrics

# Existing (from Market + Risk Spokes)
# pandas, numpy, scipy, yfinance, requests
```

### Integration Points
```python
# Market Spoke Integration
from market_spoke import unified_market_data

prices = unified_market_data(
    tickers=["AAPL", "MSFT"],
    query_type="historical",
    data_type="price",
    period="1y"
)

# Risk Spoke Integration
from risk_spoke import portfolio_risk, var_calculator

risk = portfolio_risk(
    tickers=["AAPL", "MSFT"],
    weights=[0.5, 0.5]
)
```

---

## 📈 Implementation Roadmap

### Week 1-2: Core Optimization (🔥 Highest Priority)
**Goal**: Portfolio optimization and rebalancing

**Tasks**:
1. Set up portfolio-spoke directory structure
2. Install dependencies (PyPortfolioOpt, Riskfolio-Lib)
3. Implement `portfolio_optimizer.py`
   - Mean-Variance optimization
   - HRP (Hierarchical Risk Parity)
   - Efficient frontier calculation
4. Implement `portfolio_rebalancer.py`
   - Threshold-based rebalancing
   - Trade generation
5. Create MCP server (`mcp_server.py`)
6. Write basic tests

**Deliverable**: 2 working MCP tools

---

### Week 3-4: Performance & Backtesting
**Goal**: Performance analysis and strategy simulation

**Tasks**:
1. Implement `performance_analyzer.py`
   - Return calculations
   - Sharpe, Sortino, Calmar ratios
   - Benchmark comparison
   - Attribution analysis
2. Implement `backtester.py`
   - VectorBT integration
   - Momentum strategy template
   - Equity curve generation
3. Download Fama-French factor data
4. Implement `factor_analyzer.py`
   - Factor exposure calculation
   - Factor attribution
5. Write comprehensive tests

**Deliverable**: 5 working MCP tools (cumulative)

---

### Week 5-6: Advanced Features
**Goal**: Asset allocation, tax optimization, dashboard

**Tasks**:
1. Implement `asset_allocator.py`
   - Strategic allocation
   - Multi-asset optimization
2. Implement `tax_optimizer.py`
   - Tax loss harvesting logic
   - Wash sale detection
3. Implement `portfolio_dashboard.py`
   - Aggregate all metrics
   - Health scoring
4. Create comprehensive test suite
5. Write documentation
6. Integration testing with Market + Risk Spokes

**Deliverable**: 8 working MCP tools, full test coverage

---

## 🧪 Testing Strategy

### Unit Tests (`tests/test_portfolio_tools.py`)
```python
async def test_portfolio_optimizer():
    """Test portfolio optimization"""
    result = await portfolio_optimizer(
        tickers=["AAPL", "MSFT", "GOOGL"],
        method="mean_variance",
        objective="max_sharpe"
    )
    assert "weights" in result
    assert abs(sum(result["weights"].values()) - 1.0) < 0.001  # Weights sum to 1
    assert result["sharpe_ratio"] > 0

async def test_backtester():
    """Test backtesting engine"""
    result = await backtester(
        strategy="momentum",
        universe="sp500",
        start_date="2023-01-01",
        end_date="2024-01-01"
    )
    assert "total_return" in result
    assert "equity_curve" in result
    assert len(result["equity_curve"]) > 0
```

### Integration Tests
```python
async def test_end_to_end_workflow():
    """Test complete portfolio workflow"""
    # 1. Optimize portfolio
    weights = await portfolio_optimizer(...)

    # 2. Analyze performance
    perf = await performance_analyzer(...)

    # 3. Generate rebalancing trades
    trades = await portfolio_rebalancer(...)

    # 4. Check tax implications
    tax = await tax_optimizer(...)

    # 5. Dashboard summary
    dashboard = await portfolio_dashboard(...)

    assert dashboard["health_score"] > 70
```

### Performance Benchmarks
- Optimization: < 5 seconds for 50 stocks
- Backtesting: < 30 seconds for 5-year daily backtest
- Dashboard: < 2 seconds for complete summary

---

## 🎯 Success Metrics

### Quantitative
- ✅ 8 MCP tools implemented
- ✅ 100% test coverage
- ✅ API response time < 5s (optimization)
- ✅ Support 503 S&P 500 stocks
- ✅ 5-year backtesting capability

### Qualitative
- ✅ Professional-grade optimization algorithms
- ✅ Tax optimization (unique feature)
- ✅ Factor investing support
- ✅ Comprehensive documentation
- ✅ Seamless Market + Risk Spoke integration

---

## 🔮 Future Enhancements (Post-Phase 1)

### Phase 2: Advanced Optimization
- Multi-period optimization
- Transaction cost modeling
- Conditional Value-at-Risk (CVaR) optimization
- Robust optimization (uncertainty)

### Phase 3: Machine Learning
- Reinforcement Learning for rebalancing
- LSTM price prediction integration
- Sentiment-based allocation
- Anomaly detection for risk

### Phase 4: Alternative Assets
- Real estate (REITs)
- Commodities futures
- Options strategies
- Crypto portfolio optimization

### Phase 5: Multi-Account
- Tax-location optimization
- Account aggregation
- Consolidated reporting

---

## 📋 Dependencies Map

```
Portfolio Spoke
    ├── Market Spoke (13 tools)
    │   └── unified_market_data → Price history
    ├── Risk Spoke (8 tools)
    │   ├── portfolio_risk → Risk metrics
    │   └── var_calculator → VaR calculations
    ├── External Data
    │   ├── Fama-French factors (free download)
    │   └── S&P 500 CSV files (already have)
    └── Python Libraries
        ├── PyPortfolioOpt (optimization)
        ├── Riskfolio-Lib (risk management)
        ├── VectorBT (backtesting)
        └── PyFolio (performance)
```

---

## 🚀 Getting Started

### Quick Start Commands
```bash
# 1. Navigate to portfolio spoke
cd services/portfolio-spoke

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start MCP server
python start_mcp_server.py

# 4. Test tools
python -m pytest tests/test_portfolio_tools.py -v

# 5. Add to Claude Desktop config
# See: claude_desktop_config.json
```

### Example Usage
```python
# Portfolio Optimization
result = await portfolio_optimizer(
    tickers=["AAPL", "MSFT", "GOOGL", "AMZN"],
    method="mean_variance",
    objective="max_sharpe",
    constraints={"max_weight": 0.30}
)

print(f"Optimal weights: {result['weights']}")
print(f"Expected return: {result['expected_return']:.2%}")
print(f"Sharpe ratio: {result['sharpe_ratio']:.2f}")
```

---

## 📚 References

### Academic
- Markowitz, H. (1952). Portfolio Selection. *Journal of Finance*
- De Prado, M. L. (2016). Building Diversified Portfolios that Outperform Out of Sample
- Black, F., & Litterman, R. (1992). Global Portfolio Optimization

### Libraries
- PyPortfolioOpt: https://pyportfolioopt.readthedocs.io
- Riskfolio-Lib: https://riskfolio-lib.readthedocs.io
- VectorBT: https://vectorbt.dev

### Data
- Fama-French Factors: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html
- S&P 500 Constituents: Already downloaded (503 stocks)

---

**Last Updated**: 2025-10-04
**Next Review**: After Week 2 implementation
**Owner**: Fin-Hub Development Team
