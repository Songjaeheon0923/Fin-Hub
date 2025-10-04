# 🔌 Fin-Hub API Reference

**7개 외부 API 통합 명세**

---

## 📋 API 개요

Fin-Hub는 7개의 외부 API를 통합하여 실시간 금융 데이터를 제공합니다.

| API | 상태 | 무료 티어 | 주요 기능 |
|-----|------|----------|----------|
| Alpha Vantage | ✅ Active | 25 req/day | 주식 시세, 기술 지표 |
| CoinGecko | ✅ Active | 10-30 req/min | 암호화폐 가격 |
| News API | ✅ Active | 100 req/day | 금융 뉴스 |
| FRED | ✅ Active | Unlimited | 경제 지표 |
| MarketStack | ✅ Fallback | 1000 req/month | 주식 데이터 (백업) |
| Polygon.io | 🟡 Optional | 5 req/min | 실시간 데이터 |
| Yahoo Finance | ✅ Active | Unlimited | 역사 데이터 |

---

## 1️⃣ Alpha Vantage API

### 기본 정보
- **URL**: https://www.alphavantage.co/query
- **인증**: API Key (쿼리 파라미터)
- **Rate Limit**: 5 requests/minute, 25 requests/day (free tier)
- **문서**: https://www.alphavantage.co/documentation/

### 주요 함수

#### GLOBAL_QUOTE (실시간 시세)
```
GET https://www.alphavantage.co/query
    ?function=GLOBAL_QUOTE
    &symbol=AAPL
    &apikey=YOUR_API_KEY
```

**응답 예시**:
```json
{
  "Global Quote": {
    "01. symbol": "AAPL",
    "02. open": "150.00",
    "03. high": "152.50",
    "04. low": "149.00",
    "05. price": "151.25",
    "06. volume": "50000000",
    "07. latest trading day": "2025-01-15",
    "08. previous close": "150.50",
    "09. change": "0.75",
    "10. change percent": "0.50%"
  }
}
```

**사용 도구**: `stock_quote`

---

#### TIME_SERIES_DAILY (일별 시계열)
```
GET https://www.alphavantage.co/query
    ?function=TIME_SERIES_DAILY
    &symbol=AAPL
    &outputsize=full
    &apikey=YOUR_API_KEY
```

**응답 예시**:
```json
{
  "Meta Data": {
    "1. Information": "Daily Prices (open, high, low, close) and Volumes",
    "2. Symbol": "AAPL",
    "3. Last Refreshed": "2025-01-15",
    "4. Output Size": "Full size",
    "5. Time Zone": "US/Eastern"
  },
  "Time Series (Daily)": {
    "2025-01-15": {
      "1. open": "150.00",
      "2. high": "152.50",
      "3. low": "149.00",
      "4. close": "151.25",
      "5. volume": "50000000"
    }
  }
}
```

**사용 도구**: `technical_analysis`, `stock_quote`

---

#### RSI (Relative Strength Index)
```
GET https://www.alphavantage.co/query
    ?function=RSI
    &symbol=AAPL
    &interval=daily
    &time_period=14
    &series_type=close
    &apikey=YOUR_API_KEY
```

**사용 도구**: `technical_analysis`

---

#### MACD (Moving Average Convergence Divergence)
```
GET https://www.alphavantage.co/query
    ?function=MACD
    &symbol=AAPL
    &interval=daily
    &series_type=close
    &apikey=YOUR_API_KEY
```

**사용 도구**: `technical_analysis`

---

#### SYMBOL_SEARCH (종목 검색)
```
GET https://www.alphavantage.co/query
    ?function=SYMBOL_SEARCH
    &keywords=apple
    &apikey=YOUR_API_KEY
```

**응답 예시**:
```json
{
  "bestMatches": [
    {
      "1. symbol": "AAPL",
      "2. name": "Apple Inc.",
      "3. type": "Equity",
      "4. region": "United States",
      "5. marketOpen": "09:30",
      "6. marketClose": "16:00",
      "7. timezone": "UTC-05",
      "8. currency": "USD",
      "9. matchScore": "1.0000"
    }
  ]
}
```

**사용 도구**: `stock_search`

---

#### OVERVIEW (기업 정보)
```
GET https://www.alphavantage.co/query
    ?function=OVERVIEW
    &symbol=AAPL
    &apikey=YOUR_API_KEY
```

**응답 필드**:
- Symbol, Name, Description
- Sector, Industry
- MarketCapitalization
- PERatio, DividendYield
- 52WeekHigh, 52WeekLow

**사용 도구**: `company_overview`

---

## 2️⃣ CoinGecko API

### 기본 정보
- **URL**: https://api.coingecko.com/api/v3
- **인증**: 불필요 (무료 티어)
- **Rate Limit**: 10-30 requests/minute
- **문서**: https://www.coingecko.com/en/api/documentation

### 주요 엔드포인트

#### /simple/price (암호화폐 가격)
```
GET https://api.coingecko.com/api/v3/simple/price
    ?ids=bitcoin,ethereum
    &vs_currencies=usd
    &include_24hr_change=true
    &include_market_cap=true
    &include_24hr_vol=true
```

**응답 예시**:
```json
{
  "bitcoin": {
    "usd": 45000,
    "usd_market_cap": 850000000000,
    "usd_24h_vol": 25000000000,
    "usd_24h_change": 2.5
  },
  "ethereum": {
    "usd": 3000,
    "usd_market_cap": 360000000000,
    "usd_24h_vol": 15000000000,
    "usd_24h_change": 1.8
  }
}
```

**사용 도구**: `crypto_price`, `market_overview`

---

#### /coins/list (코인 목록)
```
GET https://api.coingecko.com/api/v3/coins/list
```

**지원 코인**: 10,000+

**사용 도구**: `crypto_price`

---

## 3️⃣ News API

### 기본 정보
- **URL**: https://newsapi.org/v2
- **인증**: API Key (헤더)
- **Rate Limit**: 100 requests/day (free tier)
- **문서**: https://newsapi.org/docs

### 주요 엔드포인트

#### /everything (뉴스 검색)
```
GET https://newsapi.org/v2/everything
    ?q=Apple OR AAPL
    &language=en
    &sortBy=publishedAt
    &pageSize=100
    &apiKey=YOUR_API_KEY
```

**응답 예시**:
```json
{
  "status": "ok",
  "totalResults": 1234,
  "articles": [
    {
      "source": { "id": "bloomberg", "name": "Bloomberg" },
      "author": "John Doe",
      "title": "Apple Stock Rises on Strong iPhone Sales",
      "description": "Apple Inc. shares climbed...",
      "url": "https://bloomberg.com/...",
      "urlToImage": "https://...",
      "publishedAt": "2025-01-15T10:30:00Z",
      "content": "Full article content..."
    }
  ]
}
```

**사용 도구**: `financial_news`, `sentiment_analysis`

---

## 4️⃣ FRED (Federal Reserve Economic Data)

### 기본 정보
- **URL**: https://api.stlouisfed.org/fred
- **인증**: API Key (쿼리 파라미터)
- **Rate Limit**: Unlimited (free)
- **문서**: https://fred.stlouisfed.org/docs/api/fred/

### 주요 엔드포인트

#### /series/observations (경제 지표 데이터)
```
GET https://api.stlouisfed.org/fred/series/observations
    ?series_id=GDP
    &api_key=YOUR_API_KEY
    &file_type=json
```

**주요 지표**:
- **GDP**: 국내총생산
- **UNRATE**: 실업률
- **CPIAUCSL**: 소비자물가지수
- **FEDFUNDS**: 연방기금금리
- **DGS10**: 10년물 국채 수익률
- **DFF**: 실효 연방기금금리

**응답 예시**:
```json
{
  "observations": [
    {
      "realtime_start": "2025-01-15",
      "realtime_end": "2025-01-15",
      "date": "2024-Q3",
      "value": "23000.5"
    }
  ]
}
```

**사용 도구**: `economic_indicator`

---

## 5️⃣ MarketStack API

### 기본 정보
- **URL**: http://api.marketstack.com/v1
- **인증**: API Key (쿼리 파라미터)
- **Rate Limit**: 1,000 requests/month (free tier)
- **문서**: https://marketstack.com/documentation

### 주요 엔드포인트

#### /eod (End of Day 데이터)
```
GET http://api.marketstack.com/v1/eod
    ?access_key=YOUR_API_KEY
    &symbols=AAPL
```

**응답 예시**:
```json
{
  "data": [
    {
      "open": 150.0,
      "high": 152.5,
      "low": 149.0,
      "close": 151.25,
      "volume": 50000000,
      "adj_close": 151.25,
      "date": "2025-01-15T00:00:00+0000",
      "symbol": "AAPL",
      "exchange": "NASDAQ"
    }
  ]
}
```

**사용 도구**: `stock_quote` (fallback)

---

## 6️⃣ Polygon.io API (선택사항)

### 기본 정보
- **URL**: https://api.polygon.io
- **인증**: API Key (쿼리 파라미터)
- **Rate Limit**: 5 requests/minute (free tier)
- **문서**: https://polygon.io/docs

### 주요 엔드포인트

#### /v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{from}/{to}
```
GET https://api.polygon.io/v2/aggs/ticker/AAPL/range/1/day/2025-01-01/2025-01-15
    ?apiKey=YOUR_API_KEY
```

**사용**: 고급 실시간 데이터 (선택사항)

---

## 7️⃣ Yahoo Finance (yfinance 라이브러리)

### 기본 정보
- **라이브러리**: yfinance (Python)
- **인증**: 불필요
- **Rate Limit**: Unlimited (비공식)
- **문서**: https://github.com/ranaroussi/yfinance

### 사용 예시

```python
import yfinance as yf

# 역사 데이터 다운로드
ticker = yf.Ticker("AAPL")
hist = ticker.history(period="5y")

# 기업 정보
info = ticker.info
```

**사용**: S&P 500 데이터 다운로드, 백업 데이터 소스

---

## 🔐 API 키 관리

### 환경 변수 설정
```bash
# .env 파일
ALPHA_VANTAGE_API_KEY=your_key_here
NEWS_API_KEY=your_key_here
FRED_API_KEY=your_key_here
MARKETSTACK_API_KEY=your_key_here
POLYGON_API_KEY=your_key_here  # 선택사항
```

### 보안 주의사항
- ✅ API 키는 환경 변수로 관리
- ✅ .env 파일은 .gitignore에 추가
- ✅ 코드에 직접 하드코딩 금지
- ✅ Read-only 키 사용 권장

---

## 📊 API 사용 전략

### Fallback Chain
```
stock_quote:
  1차: Alpha Vantage
  2차: MarketStack
  3차: Local CSV (cache)
```

### Rate Limit 관리
```python
# Client-side throttling
import time

def api_call_with_rate_limit(func, *args, **kwargs):
    time.sleep(12)  # Alpha Vantage: 5 calls/min = 12sec interval
    return func(*args, **kwargs)
```

### Caching
```python
# 5분 캐시
@cache(ttl=300)
def get_stock_quote(symbol):
    return alpha_vantage.get_quote(symbol)
```

---

## 🧪 API 테스트

### Health Check
```bash
python scripts/test_all_apis.py
```

**출력**: `data/api_test_results.json`

### 개별 API 테스트
```python
# Alpha Vantage
from services.market_spoke.app.clients.alpha_vantage_client import AlphaVantageClient
client = AlphaVantageClient()
quote = client.get_quote("AAPL")

# CoinGecko
import requests
response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd")

# FRED
from fredapi import Fred
fred = Fred(api_key=os.getenv("FRED_API_KEY"))
data = fred.get_series("GDP")
```

---

## 🎯 도구별 API 매핑

### Market Spoke
| 도구 | Primary API | Fallback API |
|------|------------|--------------|
| stock_quote | Alpha Vantage | MarketStack |
| crypto_price | CoinGecko | - |
| financial_news | News API | - |
| economic_indicator | FRED | - |
| technical_analysis | Alpha Vantage | Local CSV |
| stock_search | Alpha Vantage | - |
| company_overview | Alpha Vantage | - |
| sentiment_analysis | News API | - |

### Risk Spoke
| 도구 | Data Source |
|------|------------|
| var_calculator | Local CSV or Alpha Vantage |
| risk_metrics | Local CSV or Alpha Vantage |
| portfolio_risk | Local CSV or Alpha Vantage |
| stress_testing | Local CSV (역사 데이터) |
| tail_risk | Local CSV or Alpha Vantage |
| greeks_calculator | Alpha Vantage (옵션 데이터) |

### Portfolio Spoke
| 도구 | Data Source |
|------|------------|
| portfolio_optimizer | Local CSV (S&P 500) |
| portfolio_rebalancer | Local CSV |
| performance_analyzer | Local CSV or Alpha Vantage |
| backtester | Local CSV (역사 데이터) |
| factor_analyzer | Local CSV + FRED (팩터) |
| asset_allocator | Local CSV |
| tax_optimizer | Local CSV + 거래 이력 |
| portfolio_dashboard | Local CSV or Alpha Vantage |

---

## 📈 API 사용량 모니터링

### 일일 사용량 추적
```json
{
  "date": "2025-01-15",
  "api_calls": {
    "alpha_vantage": 18,
    "coingecko": 45,
    "news_api": 12,
    "fred": 5,
    "marketstack": 0
  },
  "limits": {
    "alpha_vantage": 25,
    "news_api": 100
  },
  "remaining": {
    "alpha_vantage": 7,
    "news_api": 88
  }
}
```

---

## 🔄 API 업데이트 주기

| API | 데이터 지연 | 업데이트 주기 |
|-----|----------|-------------|
| Alpha Vantage | ~15분 | 실시간 (15분 지연) |
| CoinGecko | ~1분 | 실시간 |
| News API | ~15분 | 15분 간격 |
| FRED | 1일-1개월 | 경제 지표별 상이 |
| MarketStack | 1일 (EOD) | 일별 |

---

**마지막 업데이트**: 2025-10-04
**API 버전**: 1.0.0
**활성 API**: 6/7
**상태**: ✅ Production Ready
