# Fin-Hub API Reference for AI Integration

This document provides comprehensive API specifications for AI agents to automatically select and use appropriate APIs based on user queries and requirements.

## API Selection Criteria

### Query Classification
- **Market Data Queries**: Alpha Vantage, MarketStack
- **News/Sentiment Queries**: News API
- **Cryptocurrency Queries**: CoinGecko API
- **Economic Indicators**: FRED API
- **Compliance/Risk Queries**: OpenSanctions API

---

## 1. Alpha Vantage API
**Status**: ✅ Active | **Rate Limit**: 25 calls/day, 5 calls/minute | **Cost**: Free

### Available Functions
```python
# Real-time stock quotes
get_real_time_quote(symbol: str) -> Dict
# Returns: {symbol, price, change, change_percent, volume, timestamp}
# Use when: User asks for current stock price, live quotes, "what's AAPL trading at"

# Historical price data
get_historical_data(symbol: str, period: str = "1month") -> Dict
# Returns: {dates[], open[], high[], low[], close[], volume[], metadata}
# Use when: User asks for price history, charts, "AAPL performance last month"

# Technical indicators
get_technical_indicators(symbol: str, indicator: str = "RSI") -> Dict
# Available indicators: RSI, MACD, SMA, EMA, BBANDS, STOCH
# Returns: {dates[], values[], metadata}
# Use when: User asks for technical analysis, RSI, moving averages

# Company fundamentals
get_company_fundamentals(symbol: str) -> Dict
# Returns: {name, sector, market_cap, pe_ratio, dividend_yield, description}
# Use when: User asks about company info, "tell me about Apple"

# Symbol search
search_symbols(keywords: str) -> List[Dict]
# Returns: [{symbol, name, type, region, match_score}]
# Use when: User provides company name instead of symbol, "Tesla stock"
```

### Response Format
```json
{
  "success": true,
  "data": {...},
  "data_source": "Alpha Vantage",
  "rate_limit_remaining": 23,
  "last_updated": "2025-01-15T10:30:00Z"
}
```

### Error Handling
- **Rate limited**: Falls back to mock data with warning
- **Invalid symbol**: Returns error with suggestion
- **API down**: Falls back to MarketStack if available

---

## 2. MarketStack API
**Status**: ✅ Active | **Rate Limit**: 1000 calls/month | **Cost**: Free

### Available Functions
```python
# End-of-day prices
get_eod_data(symbols: List[str], date_from: str = None, date_to: str = None) -> Dict
# Returns: {data: [{symbol, date, open, high, low, close, volume}]}
# Use when: User asks for historical closing prices, daily data, backtesting

# Intraday prices
get_intraday_data(symbol: str, interval: str = "1hour") -> Dict
# Intervals: 1min, 5min, 10min, 15min, 30min, 1hour
# Returns: {data: [{symbol, datetime, open, high, low, close, volume}]}
# Use when: User asks for intraday data, hourly prices

# Market indices
get_indices_data(symbols: List[str] = ["SPY", "QQQ", "DIA"]) -> Dict
# Returns: Market indices data
# Use when: User asks about market performance, S&P 500, NASDAQ

# Currency exchange rates
get_currencies(base: str = "USD", symbols: List[str] = ["EUR", "GBP"]) -> Dict
# Returns: {data: [{base, symbol, rate, date}]}
# Use when: User asks about forex, currency conversion
```

### When to Use MarketStack vs Alpha Vantage
- **MarketStack**: Historical data, bulk symbol queries, currency data
- **Alpha Vantage**: Real-time quotes, technical indicators, company fundamentals

---

## 3. News API
**Status**: ✅ Active | **Rate Limit**: 1000 requests/day | **Cost**: Free

### Available Functions
```python
# Financial news search
get_financial_news(query: str = "stock market", language: str = "en",
                   page_size: int = 20, sort_by: str = "publishedAt") -> Dict
# Returns: {status, totalResults, articles: [{title, description, url, publishedAt, source}]}
# Use when: User asks for news, "latest Apple news", market updates

# Sentiment analysis ready news
get_sentiment_news(symbol: str, days_back: int = 7) -> Dict
# Returns: News articles filtered for sentiment analysis
# Use when: User asks for stock sentiment, "how do people feel about TSLA"

# Top business headlines
get_business_headlines(country: str = "us", page_size: int = 20) -> Dict
# Returns: Top business news headlines
# Use when: User asks for market overview, business news, general financial updates

# Source-specific news
get_news_by_source(sources: List[str] = ["bloomberg", "reuters"], query: str = None) -> Dict
# Available sources: bloomberg, reuters, cnbc, wall-street-journal, financial-times
# Use when: User asks for news from specific publications
```

### Sentiment Analysis Integration
```python
# AI can process news titles/descriptions for sentiment
def analyze_news_sentiment(articles: List[Dict]) -> Dict:
    # Returns: {positive: int, negative: int, neutral: int, overall_sentiment: str}
    # Use with: Any news query to provide sentiment context
```

---

## 4. CoinGecko API
**Status**: ✅ Active | **Rate Limit**: 10,000 calls/month | **Cost**: Free

### Available Functions
```python
# Cryptocurrency prices
get_crypto_prices(coin_ids: List[str], vs_currencies: List[str] = ["usd"],
                 include_24h_change: bool = True) -> Dict
# Returns: {coin_id: {currency: price, currency_24h_change: percent}}
# Use when: User asks for crypto prices, "Bitcoin price", "how's ETH doing"

# Market data
get_crypto_market_data(coin_id: str) -> Dict
# Returns: {market_cap, total_volume, price_change_24h, market_cap_rank}
# Use when: User asks about crypto market cap, trading volume

# Historical crypto data
get_crypto_history(coin_id: str, days: int = 30, interval: str = "daily") -> Dict
# Returns: {prices: [[timestamp, price]], market_caps: [], total_volumes: []}
# Use when: User asks for crypto price history, charts

# Trending cryptocurrencies
get_trending_crypto() -> Dict
# Returns: {trending: [{id, name, symbol, price_btc}]}
# Use when: User asks "what's trending in crypto", popular coins

# Crypto news
get_crypto_news() -> Dict
# Returns: Latest cryptocurrency news
# Use when: User asks for crypto news, blockchain updates
```

### Popular Coin IDs
```python
MAJOR_COINS = {
    "bitcoin": "btc",
    "ethereum": "eth",
    "cardano": "ada",
    "solana": "sol",
    "dogecoin": "doge",
    "polygon": "matic"
}
```

---

## 5. FRED API (Federal Reserve Economic Data)
**Status**: ✅ Active | **Rate Limit**: Unlimited (fair use) | **Cost**: Free

### Available Functions
```python
# Economic indicators
get_economic_indicator(series_id: str, limit: int = 100,
                      sort_order: str = "desc") -> Dict
# Returns: {observations: [{date, value}], series_info}
# Use when: User asks for economic data, GDP, unemployment, inflation

# Multiple indicators
get_multiple_indicators(series_ids: List[str]) -> Dict
# Returns: Combined data for multiple economic series
# Use when: User wants to compare economic indicators

# Series search
search_economic_data(search_text: str, limit: int = 20) -> Dict
# Returns: {seriess: [{id, title, units, frequency}]}
# Use when: User describes economic data without knowing exact series
```

### Common Economic Series IDs
```python
ECONOMIC_INDICATORS = {
    "GDP": "GDP",                    # US Gross Domestic Product
    "UNRATE": "unemployment_rate",   # US Unemployment Rate
    "CPIAUCSL": "inflation",         # US Inflation Rate (CPI)
    "FEDFUNDS": "fed_funds_rate",    # Federal Funds Rate
    "DGS10": "10_year_treasury",     # 10-Year Treasury Rate
    "DEXUSEU": "usd_eur_rate",       # USD/EUR Exchange Rate
    "HOUST": "housing_starts",       # Housing Starts
    "INDPRO": "industrial_production" # Industrial Production Index
}
```

### Usage Patterns
```python
# When user asks: "What's the unemployment rate?"
get_economic_indicator("UNRATE", limit=1)

# When user asks: "How's the economy doing?"
get_multiple_indicators(["GDP", "UNRATE", "CPIAUCSL"])
```

---

## 6. OpenSanctions API
**Status**: ✅ Active | **Rate Limit**: 1000 calls/day | **Cost**: Free

### Available Functions
```python
# Entity search (sanctions/PEP screening)
search_entities(query: str, limit: int = 10, datasets: List[str] = None) -> Dict
# Returns: {results: [{id, caption, schema, datasets, properties}]}
# Use when: User asks to check someone against sanctions, "is X sanctioned"

# Entity details
get_entity_details(entity_id: str) -> Dict
# Returns: Detailed information about sanctioned entity
# Use when: User wants more details about a flagged entity

# Dataset information
get_available_datasets() -> Dict
# Returns: List of available sanctions datasets
# Use when: User asks about data sources, coverage

# Bulk screening
screen_multiple_entities(entities: List[str]) -> Dict
# Returns: Screening results for multiple entities
# Use when: User provides list of names/companies to screen
```

### Risk Levels
```python
def assess_risk_level(match_score: float, datasets: List[str]) -> str:
    if match_score > 0.95:
        return "HIGH_RISK"
    elif match_score > 0.80:
        return "MEDIUM_RISK"
    elif match_score > 0.60:
        return "LOW_RISK"
    else:
        return "NO_RISK"
```

---

## AI Decision Tree for API Selection

### Query Analysis Framework
```python
def select_api_for_query(user_query: str) -> List[str]:
    query_lower = user_query.lower()
    selected_apis = []

    # Stock/Market related
    if any(word in query_lower for word in ['stock', 'share', 'equity', 'ticker']):
        if any(word in query_lower for word in ['price', 'quote', 'current', 'now']):
            selected_apis.append('alpha_vantage')
        if any(word in query_lower for word in ['history', 'chart', 'past', 'trend']):
            selected_apis.append('marketstack')

    # Crypto related
    if any(word in query_lower for word in ['bitcoin', 'crypto', 'ethereum', 'btc', 'eth']):
        selected_apis.append('coingecko')

    # News/Sentiment related
    if any(word in query_lower for word in ['news', 'sentiment', 'opinion', 'feeling']):
        selected_apis.append('news_api')

    # Economic related
    if any(word in query_lower for word in ['gdp', 'unemployment', 'inflation', 'fed', 'economy']):
        selected_apis.append('fred_api')

    # Risk/Compliance related
    if any(word in query_lower for word in ['sanction', 'compliance', 'risk', 'aml', 'screen']):
        selected_apis.append('opensanctions')

    return selected_apis
```

### Response Prioritization
1. **Real-time data**: Alpha Vantage > MarketStack
2. **Historical analysis**: MarketStack > Alpha Vantage
3. **Sentiment context**: Always include News API if stock mentioned
4. **Risk assessment**: Always include OpenSanctions for entity queries
5. **Economic context**: Include FRED for market-wide questions

### Error Handling Strategy
```python
def handle_api_errors(primary_api: str, backup_apis: List[str]) -> str:
    # Rate limit exceeded -> Use backup API
    # API down -> Use cached data with timestamp
    # Invalid query -> Suggest similar valid queries
    # No data found -> Broaden search or suggest alternatives
```

This reference enables AI agents to automatically select appropriate APIs, construct proper queries, handle responses, and provide comprehensive financial analysis based on user intent.