# 📊 Portfolio Spoke - Usage Guide

**Quantitative Portfolio Management for Fin-Hub**

Portfolio Spoke provides professional-grade portfolio optimization, rebalancing, and performance analysis capabilities through the Model Context Protocol (MCP).

---

## 🎯 Overview

**Current Status**: ✅ 100% Complete (All 8 tools)
**Tools Implemented**: 8 / 8
**Test Coverage**: 12/12 tests (100%)
**Dependencies**: Scipy-based (minimal external dependencies)

### Key Features

✅ **Portfolio Optimization** - Mean-Variance, HRP, Risk Parity
✅ **Rebalancing Engine** - Threshold-based, periodic, tax-aware strategies
✅ **Performance Analysis** - Sharpe, Sortino, Max Drawdown, Attribution
✅ **Backtesting** - Momentum, Mean Reversion, Equal Weight strategies
✅ **Factor Analysis** - Market, Size, Value, Momentum, Quality
✅ **Asset Allocation** - Strategic and Tactical allocation
✅ **Tax Optimization** - Tax Loss Harvesting, Wash Sale detection
✅ **Portfolio Dashboard** - Health scoring (0-100), comprehensive metrics

---

## 🚀 Quick Start

### Installation

```bash
# Navigate to portfolio-spoke directory
cd services/portfolio-spoke

# Install dependencies
pip install -r requirements.txt

# Run all tests
python tests/test_portfolio_tools.py
python tests/test_new_tools.py
python tests/test_week_5_6_tools.py
```

### Usage via MCP

```bash
# Start MCP server
python start_mcp_server.py
```

### Direct Usage (Python)

```python
from app.tools.portfolio_optimizer import portfolio_optimizer
from app.tools.portfolio_dashboard import portfolio_dashboard

# Optimize portfolio
result = await portfolio_optimizer(
    tickers=["AAPL", "MSFT", "GOOGL", "AMZN"],
    method="mean_variance",
    objective="max_sharpe"
)

print(f"Optimal weights: {result['weights']}")
print(f"Sharpe ratio: {result['sharpe_ratio']:.2f}")

# Get comprehensive dashboard
dashboard = await portfolio_dashboard(
    positions={
        "AAPL": {"shares": 100, "cost_basis": 150, "purchase_date": "2023-01-15"},
        "MSFT": {"shares": 50, "cost_basis": 300, "purchase_date": "2023-06-01"}
    },
    risk_tolerance="moderate"
)

print(f"Health Score: {dashboard['health_score']}/100")
print(f"Recommendations: {dashboard['recommendations']}")
```

---

## 🔧 MCP Tools

### 1. `portfolio_optimizer`

**Purpose**: Generate optimal portfolio weights using various optimization methods.

**Methods**:
- `mean_variance` - Markowitz Mean-Variance optimization
- `hrp` - Hierarchical Risk Parity (de Prado)
- `risk_parity` - Equal risk contribution
- `max_sharpe` - Maximum Sharpe ratio
- `min_volatility` - Minimum portfolio volatility

**Input**:
```json
{
  "tickers": ["AAPL", "MSFT", "GOOGL"],
  "method": "mean_variance",
  "objective": "max_sharpe",
  "risk_free_rate": 0.03
}
```

**Output**:
```json
{
  "weights": {"AAPL": 0.35, "MSFT": 0.40, "GOOGL": 0.25},
  "expected_return": 0.18,
  "expected_risk": 0.22,
  "sharpe_ratio": 0.68,
  "metadata": {
    "hhi": 0.335,
    "effective_assets": 2.98,
    "diversification_ratio": 1.25
  },
  "interpretation": "Portfolio optimized using Mean-Variance..."
}
```

---

### 2. `portfolio_rebalancer`

**Purpose**: Generate trade actions to rebalance portfolio to target weights.

**Strategies**:
- `threshold` - Trigger rebalancing when drift exceeds threshold
- `periodic` - Full rebalancing to target weights
- `tax_aware` - Minimize tax impact (avoid selling winners)

**Input**:
```json
{
  "current_positions": {
    "AAPL": {"shares": 100, "value": 18500, "price": 185.00}
  },
  "target_weights": {"AAPL": 0.30, "MSFT": 0.70},
  "total_value": 100000,
  "cash_available": 5000,
  "strategy": "threshold",
  "threshold": 0.05
}
```

**Output**:
```json
{
  "rebalancing_needed": true,
  "trades": [
    {
      "ticker": "AAPL",
      "action": "sell",
      "shares": 20,
      "value": 3700,
      "drift": 0.08,
      "reason": "overweight by 8%"
    }
  ],
  "total_cost": 150,
  "turnover": 0.18,
  "interpretation": "Rebalancing requires 2 trades..."
}
```

---

### 3. `performance_analyzer`

**Purpose**: Analyze portfolio performance with comprehensive metrics.

**Input**:
```json
{
  "positions": {
    "AAPL": {"shares": 100, "avg_cost": 150, "current_price": 185},
    "MSFT": {"shares": 50, "avg_cost": 300, "current_price": 420}
  },
  "benchmark": "SPY",
  "start_date": "2024-01-01"
}
```

**Output**:
```json
{
  "returns": {
    "total_return": 0.25,
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
    "excess_return": 0.05,
    "information_ratio": 0.625
  },
  "attribution": {
    "AAPL": 0.08,
    "MSFT": 0.10
  }
}
```

---

### 4. `backtester`

**Purpose**: Backtest trading strategies with realistic costs.

**Strategies**:
- `momentum` - Buy top N stocks by past returns
- `mean_reversion` - Buy oversold, sell overbought
- `equal_weight` - Equal allocation, periodic rebalancing

**Input**:
```json
{
  "strategy": "momentum",
  "universe": "sp500",
  "start_date": "2024-01-01",
  "end_date": "2024-06-01",
  "initial_capital": 100000,
  "rebalance_frequency": "monthly",
  "parameters": {
    "lookback": 60,
    "top_n": 10
  }
}
```

**Output**:
```json
{
  "performance": {
    "total_return": 0.15,
    "annualized_return": 0.32,
    "sharpe_ratio": 1.25,
    "max_drawdown": -0.08
  },
  "equity_curve": [...],
  "trades": [...],
  "metadata": {
    "total_trades": 45,
    "win_rate": 0.62,
    "turnover": 0.35
  }
}
```

---

### 5. `factor_analyzer`

**Purpose**: Analyze factor exposures and performance attribution.

**Input**:
```json
{
  "positions": {
    "AAPL": 0.35,
    "MSFT": 0.40,
    "GOOGL": 0.25
  },
  "factors": ["market", "size", "value", "momentum"],
  "start_date": "2024-01-01"
}
```

**Output**:
```json
{
  "factor_exposures": {
    "market": 1.02,
    "size": -0.15,
    "value": 0.08,
    "momentum": 0.22
  },
  "factor_returns": {
    "market": 0.12,
    "size": -0.02,
    "value": 0.01,
    "momentum": 0.03
  },
  "r_squared": 0.85,
  "alpha": 0.02
}
```

---

### 6. `asset_allocator`

**Purpose**: Allocate capital across asset classes.

**Types**:
- `strategic` - Long-term policy-based allocation
- `tactical` - Short-term market-timing allocation

**Input**:
```json
{
  "asset_classes": {
    "US_Equity": ["AAPL", "MSFT", "GOOGL"],
    "International_Equity": ["TSM"],
    "Fixed_Income": ["TLT"],
    "Commodities": ["GLD"]
  },
  "allocation_type": "strategic",
  "risk_tolerance": "moderate"
}
```

**Output**:
```json
{
  "allocation": {
    "US_Equity": 0.45,
    "International_Equity": 0.15,
    "Fixed_Income": 0.25,
    "Commodities": 0.15
  },
  "diversification": {
    "effective_assets": 8.5,
    "concentration_risk": "Low"
  },
  "correlation_analysis": {
    "average_correlation": 0.35
  },
  "expected_return": 0.08,
  "sharpe_ratio": 0.42
}
```

---

### 7. `tax_optimizer`

**Purpose**: Optimize portfolio for tax efficiency.

**Input**:
```json
{
  "positions": {
    "AAPL": {
      "shares": 100,
      "cost_basis": 150,
      "current_price": 185,
      "purchase_date": "2023-01-15"
    }
  },
  "transactions": [...],
  "tax_bracket": 0.24,
  "ltcg_rate": 0.15
}
```

**Output**:
```json
{
  "tax_loss_harvest_opportunities": [
    {
      "ticker": "TSLA",
      "unrealized_loss": -2500,
      "tax_benefit": 600,
      "holding_period": "short"
    }
  ],
  "wash_sale_warnings": [...],
  "long_term_gains": 5000,
  "short_term_gains": -2000,
  "potential_tax_savings": 1200,
  "recommendations": [...]
}
```

---

### 8. `portfolio_dashboard`

**Purpose**: Comprehensive portfolio health check and recommendations.

**Input**:
```json
{
  "positions": {
    "AAPL": {
      "shares": 100,
      "cost_basis": 150,
      "current_price": 185,
      "purchase_date": "2023-01-15"
    }
  },
  "target_weights": {"AAPL": 0.33, "MSFT": 0.33, "GOOGL": 0.34},
  "risk_tolerance": "moderate"
}
```

**Output**:
```json
{
  "health_score": 85,
  "health_grade": "B",
  "health_components": {
    "performance": 30,
    "risk_management": 25,
    "diversification": 20,
    "rebalancing": 15,
    "tax_efficiency": 10
  },
  "portfolio_value": 50000,
  "performance": {...},
  "risk_assessment": {...},
  "diversification": {...},
  "rebalancing": {
    "needed": true,
    "max_drift": 0.08
  },
  "tax_efficiency": {...},
  "recommendations": [...],
  "alerts": [...]
}
```

---

## 📁 Project Structure

```
services/portfolio-spoke/
├── app/
│   ├── tools/                       # MCP tools (8 total)
│   │   ├── portfolio_optimizer.py   # ✅ Mean-Variance, HRP, Risk Parity
│   │   ├── portfolio_rebalancer.py  # ✅ Threshold, Periodic, Tax-aware
│   │   ├── performance_analyzer.py  # ✅ Returns, Sharpe, Attribution
│   │   ├── backtester.py            # ✅ Momentum, Mean Reversion
│   │   ├── factor_analyzer.py       # ✅ Factor exposure analysis
│   │   ├── asset_allocator.py       # ✅ Strategic/Tactical allocation
│   │   ├── tax_optimizer.py         # ✅ Tax loss harvesting
│   │   └── portfolio_dashboard.py   # ✅ Health scoring
│   └── utils/
│       ├── data_loader.py           # ✅ S&P 500 data loading
│       └── portfolio_math.py        # ✅ Core calculations
├── mcp_server.py                    # ✅ MCP server (8 tools)
├── start_mcp_server.py              # ✅ Launcher
├── requirements.txt                 # ✅ Dependencies
└── tests/
    ├── test_portfolio_tools.py      # ✅ Week 1-2 (6 tests)
    ├── test_new_tools.py            # ✅ Week 3-4 (3 tests)
    └── test_week_5_6_tools.py       # ✅ Week 5-6 (3 tests)
```

---

## 🧪 Testing

### Run All Tests

```bash
# Week 1-2 tests
python tests/test_portfolio_tools.py

# Week 3-4 tests
python tests/test_new_tools.py

# Week 5-6 tests
python tests/test_week_5_6_tools.py
```

### Test Coverage

| Test | Status | Description |
|------|--------|-------------|
| Portfolio Optimizer - Max Sharpe | ✅ | Maximize Sharpe ratio |
| Portfolio Optimizer - Min Volatility | ✅ | Minimize portfolio risk |
| Portfolio Optimizer - HRP | ✅ | Hierarchical Risk Parity |
| Portfolio Optimizer - Risk Parity | ✅ | Equal risk contribution |
| Portfolio Rebalancer - Threshold | ✅ | Threshold-based rebalancing |
| Portfolio Rebalancer - No Rebalance | ✅ | Skip when within bands |
| Performance Analyzer | ✅ | Returns, Sharpe, Attribution |
| Backtester | ✅ | Momentum strategy |
| Factor Analyzer | ✅ | Factor exposures |
| Asset Allocator | ✅ | Strategic allocation |
| Tax Optimizer | ✅ | Tax loss harvesting |
| Portfolio Dashboard | ✅ | Health scoring |

**Success Rate**: 100% (12/12 tests)

---

## 📊 Data Requirements

### Available Data ✅
- **S&P 500 Stocks**: 503 tickers, 5 years daily OHLCV (71 MB)
- **Market Data**: Via Market Spoke (13 tools)
- **Risk Metrics**: Via Risk Spoke (8 tools)
- **Crypto Prices**: CoinGecko API
- **Economic Indicators**: FRED API

### Data Location
- CSV files: `data/stock-data/*.csv`
- Metadata: `data/stock-data/_metadata.json`
- Tickers: `data/stock-data/sp500_tickers.json`

---

## 🛠️ Dependencies

### Core Libraries (Minimal)
```
scipy >= 1.11.0              # Optimization algorithms
pandas >= 2.0.0              # Data manipulation
numpy >= 1.24.0              # Numerical computations
scikit-learn >= 1.3.0        # Covariance estimation
```

### Install All
```bash
pip install -r requirements.txt
```

**Note**: Portfolio Spoke uses scipy-based implementations to minimize external dependencies and avoid compilation issues.

---

## 🎯 Design Principles

### 1. Professional-Grade Algorithms
- Academic research-based (Markowitz, de Prado, Black-Litterman)
- Industry-standard methodologies
- Scipy-based optimization (SLSQP method)

### 2. Quantitative Focus
- MCP protocol integration (unique)
- Programmable portfolio management
- API-first design

### 3. Integration with Existing Spokes
- Market Spoke → Price data (13 tools)
- Risk Spoke → Risk metrics (8 tools)
- Seamless data flow

### 4. Tax Optimization
- Tax loss harvesting
- Wash sale detection (30-day rule)
- LTCG vs STCG classification
- Tax benefit calculations

---

## 🔗 Integration with Fin-Hub

### Spoke Dependencies

```
Portfolio Spoke (8 tools)
    ├── Market Spoke (13 tools)
    │   └── unified_market_data → Price history
    ├── Risk Spoke (8 tools)
    │   ├── portfolio_risk → Risk metrics
    │   └── var_calculator → VaR calculations
    └── Data
        └── S&P 500 CSV (503 stocks, 5 years)
```

### MCP Configuration

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "portfolio-spoke": {
      "command": "python",
      "args": [
        "C:/project/Fin-Hub/services/portfolio-spoke/start_mcp_server.py"
      ]
    }
  }
}
```

---

## 📝 Usage Examples

### Example 1: Optimize Tech Portfolio

```python
result = await portfolio_optimizer(
    tickers=["AAPL", "MSFT", "GOOGL", "NVDA", "META"],
    method="mean_variance",
    objective="max_sharpe",
    constraints={"max_weight": 0.30}  # Max 30% per stock
)

print(f"Optimal allocation: {result['weights']}")
# Expected: Diversified across 5 tech stocks with max 30% each
```

### Example 2: Backtest Momentum Strategy

```python
result = await backtester(
    strategy="momentum",
    universe="sp500",
    start_date="2024-01-01",
    end_date="2024-06-01",
    initial_capital=100000,
    rebalance_frequency="monthly",
    parameters={"lookback": 60, "top_n": 10}
)

print(f"Total Return: {result['performance']['total_return']:.2%}")
print(f"Sharpe Ratio: {result['performance']['sharpe_ratio']:.2f}")
```

### Example 3: Tax Loss Harvesting

```python
result = await tax_optimizer(
    positions={
        "TSLA": {
            "shares": 50,
            "cost_basis": 250,
            "current_price": 200,
            "purchase_date": "2024-03-01"
        }
    },
    transactions=[...],
    tax_bracket=0.24
)

print(f"TLH Opportunities: {len(result['tax_loss_harvest_opportunities'])}")
print(f"Potential Savings: ${result['potential_tax_savings']:.2f}")
```

### Example 4: Portfolio Health Check

```python
dashboard = await portfolio_dashboard(
    positions={
        "AAPL": {"shares": 100, "cost_basis": 150, "purchase_date": "2023-01-15"},
        "MSFT": {"shares": 50, "cost_basis": 300, "purchase_date": "2023-06-01"},
        "GOOGL": {"shares": 80, "cost_basis": 120, "purchase_date": "2023-03-01"}
    },
    target_weights={"AAPL": 0.33, "MSFT": 0.33, "GOOGL": 0.34},
    risk_tolerance="moderate"
)

print(f"Health Score: {dashboard['health_score']}/100 (Grade: {dashboard['health_grade']})")
print(f"Portfolio Value: ${dashboard['portfolio_value']:,.2f}")
print(f"Rebalancing Needed: {dashboard['rebalancing']['needed']}")
print(f"\nRecommendations:")
for rec in dashboard['recommendations']:
    print(f"  • {rec}")
```

---

## 📚 References

### Academic
- Markowitz, H. (1952). Portfolio Selection. *Journal of Finance*
- De Prado, M. L. (2016). Building Diversified Portfolios
- Fama, E. F., & French, K. R. (1993). Common risk factors

### Documentation
- [Scipy Optimization](https://docs.scipy.org/doc/scipy/reference/optimize.html)
- [Modern Portfolio Theory](https://en.wikipedia.org/wiki/Modern_portfolio_theory)
- [Tax Loss Harvesting](https://www.investopedia.com/terms/t/taxgainlossharvesting.asp)

---

**Last Updated**: 2025-10-04
**Version**: 1.0.0 (100% Complete)
**Status**: Production ready, all 8 tools implemented
**Next Steps**: Integrate with Hub Server, Docker deployment
