# 📦 Fin-Hub Dataset Reference

**로컬 데이터셋 및 외부 API 완전 참조**

---

## 📊 로컬 데이터셋

### S&P 500 주식 데이터

**위치**: `data/stock-data/`
**크기**: 71.4 MB
**종목 수**: 503개 (S&P 500 전체)
**기간**: 5년 (2020-01-01 ~ 2025-01-15)
**빈도**: 일별 (Daily)

#### 데이터 구조
```csv
Date,Open,High,Low,Close,Volume,Adj Close
2020-01-02,74.06,75.15,73.80,75.09,135480400,73.04
2020-01-03,74.29,75.14,74.13,74.36,146322800,72.33
...
```

#### 컬럼 설명
- **Date**: 거래일 (YYYY-MM-DD)
- **Open**: 시가
- **High**: 고가
- **Low**: 저가
- **Close**: 종가
- **Volume**: 거래량
- **Adj Close**: 조정 종가 (배당/분할 반영)

#### 메타데이터
**파일**: `data/stock-data/_metadata.json`
```json
{
  "total_stocks": 503,
  "total_size_mb": 71.4,
  "date_range": {
    "start": "2020-01-01",
    "end": "2025-01-15"
  },
  "data_quality": {
    "missing_data_pct": 0.02,
    "completeness": 99.98
  }
}
```

#### 주요 종목 예시
- **AAPL**: Apple Inc. (2.5 MB, 1,260 rows)
- **MSFT**: Microsoft Corp. (2.3 MB, 1,260 rows)
- **GOOGL**: Alphabet Inc. (2.4 MB, 1,260 rows)
- **TSLA**: Tesla Inc. (2.6 MB, 1,260 rows)
- **NVDA**: NVIDIA Corp. (2.5 MB, 1,260 rows)

---

## 🔌 외부 API 통합

### 1. Alpha Vantage
**URL**: https://www.alphavantage.co/
**상태**: ✅ Active
**무료 티어**: 25 requests/day, 5 requests/minute

**기능**:
- 실시간 주식 시세 (GLOBAL_QUOTE)
- 일별/주별/월별 시계열 (TIME_SERIES_*)
- 기술 지표 (RSI, MACD, SMA)
- 종목 검색 (SYMBOL_SEARCH)
- 기업 정보 (OVERVIEW)

**사용 도구**:
- `stock_quote`
- `technical_analysis`
- `stock_search`
- `company_overview`

---

### 2. CoinGecko
**URL**: https://www.coingecko.com/
**상태**: ✅ Active
**무료 티어**: 10-30 calls/minute

**기능**:
- 암호화폐 가격 (10,000+ 코인)
- 시가총액, 거래량
- 24시간 변동률
- 역사 데이터

**사용 도구**:
- `crypto_price`
- `unified_market_data`
- `market_overview`

---

### 3. News API
**URL**: https://newsapi.org/
**상태**: ✅ Active
**무료 티어**: 100 requests/day

**기능**:
- 금융 뉴스 검색
- 키워드 필터링
- 날짜 범위 지정
- 소스별 검색

**사용 도구**:
- `financial_news`
- `sentiment_analysis`
- `market_overview`

---

### 4. FRED (Federal Reserve Economic Data)
**URL**: https://fred.stlouisfed.org/
**상태**: ✅ Active
**무료 티어**: Unlimited

**기능**:
- 경제 지표 (GDP, CPI, 실업률)
- 연방기금금리
- 역사 데이터 (50+ years)
- 고빈도 업데이트

**주요 지표**:
- **GDP**: 국내총생산
- **UNRATE**: 실업률
- **CPIAUCSL**: 소비자물가지수
- **FEDFUNDS**: 연방기금금리
- **DGS10**: 10년물 국채 수익률

**사용 도구**:
- `economic_indicator`
- `unified_market_data`

---

### 5. MarketStack
**URL**: https://marketstack.com/
**상태**: ✅ Active (Fallback)
**무료 티어**: 1,000 requests/month

**기능**:
- 주식 시세 (Alpha Vantage 대체)
- EOD (End of Day) 데이터
- Intraday 데이터

**사용 도구**:
- `stock_quote` (fallback)

---

### 6. Polygon.io
**URL**: https://polygon.io/
**상태**: 🟡 Optional
**무료 티어**: 5 calls/minute

**기능**:
- 실시간 주식/옵션/암호화폐 데이터
- Aggregates (OHLCV)
- 티커 정보

**사용 도구**:
- (선택적 사용)

---

### 7. Yahoo Finance (yfinance)
**URL**: https://finance.yahoo.com/
**상태**: ✅ Active (Library)
**무료 티어**: Unlimited (비공식)

**기능**:
- 역사 가격 데이터
- 실시간 시세
- 배당 정보
- 기업 정보

**사용 도구**:
- 내부 데이터 수집용

---

## 📁 데이터 파일 목록

### 주요 데이터셋
```
data/
├── stock-data/              # S&P 500 주식 데이터
│   ├── AAPL.csv            # Apple Inc.
│   ├── MSFT.csv            # Microsoft
│   ├── GOOGL.csv           # Alphabet
│   ├── TSLA.csv            # Tesla
│   ├── NVDA.csv            # NVIDIA
│   ├── ... (503 files)
│   ├── _metadata.json      # 메타데이터
│   └── sp500_tickers.json  # 티커 목록
├── crypto-cache/            # 암호화폐 캐시 (임시)
├── api_test_results.json   # API 테스트 결과
└── validation_report.json  # 데이터 검증 리포트
```

---

## 🔍 데이터 품질

### 검증 결과 (2025-10-04)

**S&P 500 데이터**:
- ✅ 503/503 종목 완료 (100%)
- ✅ 결측치: 0.02% (무시 가능)
- ✅ 이상치: 검증 완료
- ✅ 날짜 일관성: 정상
- ✅ 가격 범위: 정상

**API 상태**:
- ✅ Alpha Vantage: 정상
- ✅ CoinGecko: 정상
- ✅ News API: 정상
- ✅ FRED: 정상
- ✅ MarketStack: 정상 (fallback)

---

## 📥 데이터 다운로드 가이드

### S&P 500 데이터 재다운로드
```bash
cd scripts
python download_sp500_full.py
```

**소요 시간**: ~30분 (503개 종목)
**저장 위치**: `data/stock-data/`

### 데이터 검증
```bash
python validate_and_analyze_data.py
```

**출력**: `data/validation_report.json`

---

## 🎯 데이터 사용 예시

### Market Spoke
```python
# S&P 500 로컬 데이터 사용
df = pd.read_csv('data/stock-data/AAPL.csv')

# API로 실시간 데이터 가져오기
quote = alpha_vantage.get_quote('AAPL')
```

### Risk Spoke
```python
# 30일 가격 데이터로 VaR 계산
prices = df['Close'].tail(30)
var_95 = calculate_var(prices, confidence=0.95)
```

### Portfolio Spoke
```python
# 여러 종목 데이터 로드
tickers = ['AAPL', 'MSFT', 'GOOGL']
prices = {}
for ticker in tickers:
    prices[ticker] = pd.read_csv(f'data/stock-data/{ticker}.csv')

# 포트폴리오 최적화
weights = optimize_portfolio(prices)
```

---

## 🔧 캐싱 전략

### In-Memory Cache
- **TTL**: 5분 (주식/암호화폐)
- **TTL**: 15분 (뉴스)
- **저장소**: 메모리 (Redis 선택사항)

### Disk Cache
- **위치**: `data/crypto-cache/`
- **형식**: JSON
- **자동 정리**: 24시간마다

---

## 📊 데이터 업데이트 주기

| 데이터 유형 | 업데이트 주기 | 소스 |
|------------|-------------|------|
| S&P 500 주식 | 일별 (EOD) | 로컬 CSV |
| 실시간 시세 | 실시간 | Alpha Vantage API |
| 암호화폐 | 5분 | CoinGecko API |
| 뉴스 | 15분 | News API |
| 경제 지표 | 월별/분기별 | FRED API |

---

## 🎯 데이터 요구사항 (도구별)

### Market Spoke
- **필수**: S&P 500 CSV 또는 Alpha Vantage API
- **선택**: CoinGecko, News API, FRED

### Risk Spoke
- **필수**: 최소 30일 가격 데이터
- **권장**: 1년+ 데이터 (스트레스 테스트)

### Portfolio Spoke
- **필수**: 1년+ 가격 데이터 (백테스팅)
- **선택**: 거래 이력 (세금 최적화)

---

**마지막 업데이트**: 2025-10-04
**데이터 버전**: 1.0.0
**총 용량**: 71.4 MB (로컬)
**API 통합**: 7개 (6개 활성)
