# 📊 Fin-Hub 데이터 & API 완벽 가이드

> **업데이트:** 2025-10-04
> **상태:** 프로덕션 준비 완료

---

## 📑 목차

1. [로컬 데이터셋](#1-로컬-데이터셋)
2. [실시간 API](#2-실시간-api)
3. [MCP 도구 매핑](#3-mcp-도구-매핑)
4. [데이터 다운로드 가이드](#4-데이터-다운로드-가이드)
5. [사용 예제](#5-사용-예제)

---

## 1. 로컬 데이터셋

### 📈 S&P 500 주식 데이터 ✅ 완료

| 항목 | 정보 |
|------|------|
| **위치** | `D:\project\Fin-Hub\data\stock-data\` |
| **파일 수** | 503개 CSV 파일 |
| **크기** | 71 MB |
| **기간** | 2020-10-05 ~ 2025-10-04 (5년) |
| **간격** | 일별 (Daily) |
| **레코드/주식** | ~1,256개 |
| **총 레코드** | ~633,000개 |
| **검증 상태** | ✅ 100% 통과 |

**데이터 구조:**
```csv
Date, Open, High, Low, Close, Volume, Dividends, Stock Splits
```

**주요 종목:**
- Tech: AAPL, MSFT, GOOGL, AMZN, META, NVDA, TSLA
- Finance: JPM, BAC, V, MA
- Healthcare: JNJ, UNH, PFE
- Consumer: WMT, HD, MCD, DIS
- ...총 503개

**다운로드 방법:**
```bash
python scripts/download_sp500_full.py --yes
```

**사용하는 MCP 도구:**
- 없음 (로컬 분석용)
- Python pandas로 직접 읽기

**사용 예제:**
```python
import pandas as pd

# AAPL 5년 데이터 로드
df = pd.read_csv("data/stock-data/AAPL.csv", index_col=0, parse_dates=True)

# 백테스팅, 기술적 분석 등 가능
print(df.describe())
```

---

### 💰 암호화폐 캐시 데이터 ⚠️ 부분

| 항목 | 정보 |
|------|------|
| **위치** | `D:\project\Fin-Hub\data\crypto-cache\` |
| **파일 수** | 6개 JSON 파일 |
| **크기** | 365 KB |
| **상태** | 4/6 경고 (구조 문제) |
| **대안** | CoinGecko API 사용 중 ✅ |

**파일 목록:**
- `bitcoin_data.json` (76 KB) - ⚠️
- `ethereum_data.json` (76 KB) - ⚠️
- `ripple_data.json` (77 KB) - ⚠️
- `tether_data.json` (77 KB) - ⚠️
- `market_overview.json` (48 KB) - ✅
- `_metadata.json` (539 B)

**문제:** 가격 데이터 구조 불일치
**해결:** CoinGecko API로 실시간 조회 (자동 대체)

---

### 🏦 Gekko 암호화폐 역사 데이터 ⏳ 선택

| 항목 | 정보 |
|------|------|
| **위치** | `D:\project\Fin-Hub\data\gekko-history\` |
| **상태** | 비어있음 (다운로드 필요) |
| **크기 (옵션 1)** | 100 MB (30일 데이터) |
| **크기 (옵션 2)** | 3 GB (전체 역사) |
| **용도** | 백테스팅, 역사 분석 |
| **필요성** | 선택사항 |

**다운로드 링크:**
- 30일 데이터: https://drive.google.com/drive/folders/1Ghoy6w3BfHNgoRjj5jI9dX1BV0WyS8l_
- 전체 역사: https://drive.google.com/drive/folders/1KiYD4jLRwwDkE6GWyQXLz-Lz59H3h_2v

**다운로드 방법:**
1. 위 링크에서 `binance_30d.zip` 다운로드
2. `data/gekko-history/`로 이동
3. 압축 해제: `Expand-Archive binance_30d.zip`
4. 검증: `python scripts/gekko_data_integration.py`

**데이터 내용:**
- 200+ 거래쌍
- SQLite 데이터베이스
- OHLCV 캔들 데이터

---

## 2. 실시간 API

### API 1: Finnhub ⚠️

| 항목 | 정보 |
|------|------|
| **상태** | 설정됨 (Fallback으로 작동) |
| **키** | `d3bpft1r01qqg7bvjb4g...vjb50` |
| **플랜** | Free |
| **제한** | - |
| **문서** | https://finnhub.io/docs/api |

**제공 데이터:**
- 실시간 주가 (Quote)
- 회사 프로필
- 재무 제표
- 뉴스
- 기술적 지표

**사용하는 MCP 도구:**
- `market.get_stock_quote` (Primary, 현재 실패 시 fallback)

**현재 상태:**
- ⚠️ 환경변수 로딩 문제로 직접 작동 안 함
- ✅ Alpha Vantage로 자동 fallback 작동 중

**API 호출 예시:**
```python
# UnifiedAPIManager가 자동으로 fallback 처리
async with UnifiedAPIManager() as api:
    quote = await api.get_stock_quote("AAPL")
    # Finnhub 실패 → Alpha Vantage 자동 사용
```

---

### API 2: Alpha Vantage ✅ 메인

| 항목 | 정보 |
|------|------|
| **상태** | ✅ 활성 (현재 메인으로 사용) |
| **키** | `26PNNX3GELI0JE1W` |
| **플랜** | Free |
| **제한** | 500 calls/day |
| **문서** | https://www.alphavantage.co/documentation/ |

**제공 데이터:**
- 실시간 주가 (GLOBAL_QUOTE)
- 일별/주별/월별 OHLCV
- 기술적 지표 (SMA, EMA, RSI 등)
- 외환 (Forex)

**사용하는 MCP 도구:**
- `market.get_stock_quote` (현재 Primary로 작동)
- `market.get_unified_data` (stock 타입)

**테스트 결과:**
```
AAPL: $257.13 (+0.66%)
응답 시간: ~0.5초
성공률: 100%
```

**API 호출 예시:**
```python
async with UnifiedAPIManager() as api:
    quote = await api.get_stock_quote("TSLA")
    print(f"{quote['symbol']}: ${quote['price']:.2f}")
```

---

### API 3: MarketStack 🔸

| 항목 | 정보 |
|------|------|
| **상태** | 설정됨 (Last resort) |
| **키** | `4b0b39b5e85893449a6d3c724208414e` |
| **플랜** | Free |
| **제한** | 100 calls/month |
| **문서** | https://marketstack.com/documentation |

**제공 데이터:**
- EOD (End of Day) 주가
- 역사 데이터
- 60+ 거래소

**사용하는 MCP 도구:**
- `market.get_stock_quote` (Tertiary fallback)

**역할:**
- Finnhub, Alpha Vantage 모두 실패 시 마지막 수단

---

### API 4: CoinGecko ✅ 암호화폐

| 항목 | 정보 |
|------|------|
| **상태** | ✅ 활성 |
| **키** | `CG-7m3WhvdkzRv7mKDxv6cSiAvA` |
| **플랜** | Pro (유료) |
| **제한** | - |
| **문서** | https://www.coingecko.com/api/documentation |

**제공 데이터:**
- 실시간 암호화폐 가격
- 24시간 변동, 거래량, 시가총액
- 13,000+ 코인 지원

**사용하는 MCP 도구:**
- `market.get_crypto_price`
- `market.get_overview` (crypto 섹션)
- `market.get_unified_data` (crypto 타입)

**캐싱:**
- ✅ 5분 TTL
- 동일 요청 시 캐시에서 즉시 반환

**테스트 결과:**
```
Bitcoin: $121,376 (+1.90%)
Ethereum: $4,489 (+2.13%)
응답 시간: ~0.5초 (첫 요청), ~0.001초 (캐시)
```

**API 호출 예시:**
```python
async with UnifiedAPIManager() as api:
    btc = await api.get_crypto_price("bitcoin")
    eth = await api.get_crypto_price("ethereum")
```

---

### API 5: News API ✅ 뉴스

| 항목 | 정보 |
|------|------|
| **상태** | ✅ 활성 |
| **키** | `405f5be781ea43f8bcc968bbed21ce5b` |
| **플랜** | Free |
| **제한** | - |
| **문서** | https://newsapi.org/docs |

**제공 데이터:**
- 금융 뉴스 (실시간)
- 80,000+ 뉴스 소스
- 150개국 커버리지

**사용하는 MCP 도구:**
- `market.get_financial_news`
- `market.get_overview` (news 섹션)
- `market.get_unified_data` (news 타입)

**추가 기능:**
- ✅ 자동 감성 분석 (긍정/부정/중립)
- 키워드 기반 분류

**테스트 결과:**
```
Query: "AI stocks"
Found: 3 articles
Sentiment: neutral, neutral, positive
응답 시간: ~0.4초
```

**API 호출 예시:**
```python
async with UnifiedAPIManager() as api:
    news = await api.get_financial_news("tech stocks", page_size=10)
    for article in news:
        print(f"{article['title']} - {article['sentiment']}")
```

---

### API 6: FRED ✅ 경제 지표

| 항목 | 정보 |
|------|------|
| **상태** | ✅ 활성 |
| **키** | `92724a95d566630ad9fa1757fc672702` |
| **플랜** | Free |
| **제한** | 무제한 |
| **문서** | https://fred.stlouisfed.org/docs/api/ |

**제공 데이터:**
- 841,000개 경제 시계열
- GDP, 실업률, 인플레이션
- 금리 (Fed Funds Rate, Treasury Yields)
- 환율, 주택, 제조업 지표
- 50년 역사 데이터

**사용하는 MCP 도구:**
- `market.get_economic_indicator`
- `market.get_overview` (economic 섹션)
- `market.get_unified_data` (economic 타입)

**주요 시리즈 ID:**
- `GDP` - 국내총생산
- `UNRATE` - 실업률
- `CPIAUCSL` - 소비자물가지수
- `DFF` - 연방기금금리
- `DGS10` - 10년 국채 수익률

**테스트 결과:**
```
Series: GDP
Latest: $30,485.7B (2025-Q1)
응답 시간: ~0.5초
```

**API 호출 예시:**
```python
async with UnifiedAPIManager() as api:
    gdp = await api.get_economic_indicator("GDP", limit=5)
    unemployment = await api.get_economic_indicator("UNRATE", limit=12)
```

---

### API 7: OpenSanctions ✅ 컴플라이언스

| 항목 | 정보 |
|------|------|
| **상태** | ✅ 활성 |
| **키** | `f4a7e5b75a07f93a98a9ecb4656770f8` |
| **플랜** | Free |
| **제한** | - |
| **문서** | https://www.opensanctions.org/docs/api/ |

**제공 데이터:**
- 국제 제재 목록
- 정치적 주요 인물 (PEP)
- 범죄자 데이터베이스

**사용하는 MCP 도구:**
- `market.get_unified_data` (sanctions 타입)
- (전용 도구는 없음, 범용 도구 사용)

**용도:**
- KYC (Know Your Customer)
- AML (Anti-Money Laundering)
- 컴플라이언스 체크

**테스트 결과:**
```
Query: "Vladimir Putin"
Results: 1,251 matches
응답 시간: ~0.5초
```

---

## 3. MCP 도구 매핑

### Market Spoke 도구 (10개)

#### 1. `market.get_stock_quote`

**기능:** 실시간 주식 가격 조회

**사용 API:**
- Primary: Finnhub (현재 실패)
- Secondary: Alpha Vantage ✅ 현재 사용
- Tertiary: MarketStack

**입력:**
```json
{"symbol": "AAPL"}
```

**출력:**
```json
{
  "symbol": "AAPL",
  "price": 257.13,
  "change": 1.68,
  "change_percent": 0.66,
  "high": 258.18,
  "low": 254.15,
  "open": 255.45,
  "volume": 45678900,
  "timestamp": "2025-10-04T15:30:00Z",
  "source": "alpha_vantage"
}
```

**사용 데이터:**
- 실시간 API만 사용 (로컬 데이터 미사용)

---

#### 2. `market.get_crypto_price`

**기능:** 암호화폐 가격 조회

**사용 API:**
- CoinGecko ✅

**입력:**
```json
{"coin_id": "bitcoin"}
```

**출력:**
```json
{
  "coin_id": "bitcoin",
  "price": 121376.00,
  "change_24h": 1.90,
  "volume_24h": 67566624907,
  "market_cap": 2410580206855,
  "timestamp": "2025-10-04T15:30:00Z",
  "source": "coingecko"
}
```

**사용 데이터:**
- CoinGecko API (실시간)
- 로컬 캐시 (5분 TTL)

---

#### 3. `market.get_financial_news`

**기능:** 금융 뉴스 검색 + 감성 분석

**사용 API:**
- News API ✅

**입력:**
```json
{"query": "AI stocks", "page_size": 10}
```

**출력:**
```json
{
  "articles": [
    {
      "title": "Stock market today: Dow, S&P 500...",
      "description": "...",
      "url": "https://...",
      "source": "Yahoo Finance",
      "published_at": "2025-10-04T14:30:00Z",
      "sentiment": "neutral"
    }
  ],
  "count": 10
}
```

**사용 데이터:**
- News API (실시간)
- 자동 감성 분석 (로컬 처리)

---

#### 4. `market.get_economic_indicator`

**기능:** 경제 지표 조회

**사용 API:**
- FRED ✅

**입력:**
```json
{"series_id": "GDP", "limit": 10}
```

**출력:**
```json
{
  "series_id": "GDP",
  "observations": [
    {"date": "2025-04-01", "value": "30485.729"},
    {"date": "2025-01-01", "value": "30042.113"}
  ],
  "timestamp": "2025-10-04T15:30:00Z",
  "source": "fred"
}
```

**사용 데이터:**
- FRED API (실시간)

---

#### 5. `market.get_overview`

**기능:** 종합 시장 대시보드

**사용 API:**
- Alpha Vantage (주요 지수: SPY, QQQ, DIA)
- CoinGecko (BTC, ETH)
- News API (최신 뉴스 5개)
- FRED (GDP)

**입력:**
```json
{}
```

**출력:**
```json
{
  "timestamp": "2025-10-04T15:30:00Z",
  "indices": {
    "sp500": {"price": 669.22, "change_percent": 0.12},
    "nasdaq": {"price": 605.73, "change_percent": 0.41},
    "dow": {"price": 465.11, "change_percent": 0.18}
  },
  "crypto": {
    "bitcoin": {"price": 121376, "change_24h": 1.90},
    "ethereum": {"price": 4489.49, "change_24h": 2.13}
  },
  "news": [...],
  "economic": {
    "gdp": {...}
  }
}
```

**사용 데이터:**
- 4개 API 병렬 호출
- 모든 데이터 실시간

---

#### 6. `market.get_api_status`

**기능:** API 헬스 체크

**사용 API:**
- 모든 API 상태 확인

**출력:**
```json
{
  "apis": {
    "finnhub": {"available": false},
    "alpha_vantage": {"available": true},
    "coingecko": {"available": true},
    ...
  },
  "configured_keys": {
    "finnhub": false,
    "alpha_vantage": true,
    ...
  }
}
```

---

#### 7. `market.get_unified_data`

**기능:** 범용 데이터 접근

**지원 타입:**
- `stock` - 주식 (API 1, 2, 3)
- `crypto` - 암호화폐 (API 4)
- `news` - 뉴스 (API 5)
- `economic` - 경제 (API 6)
- `sanctions` - 제재 (API 7)
- `batch` - 배치 조회
- `overview` - 종합 대시보드

---

#### 8-10. 기본 분석 도구

- `market.get_price` (PriceAnalyzer) - 가격 분석
- `market.predict_volatility` (VolatilityPredictor) - 변동성 예측
- `market.analyze_sentiment` (SentimentAnalyzer) - 감성 분석

**상태:** 구현됨, 추가 테스트 필요

---

## 4. 데이터 다운로드 가이드

### S&P 500 주식 데이터

```bash
# 자동 다운로드 (추천)
python scripts/download_sp500_full.py --yes

# 수동으로 제어
python scripts/download_sp500_full.py

# 다운로드 후 검증
python scripts/validate_and_analyze_data.py
```

**소요 시간:** 60초
**다운로드 크기:** 71 MB
**최종 위치:** `data/stock-data/*.csv`

---

### Gekko 암호화폐 데이터 (선택)

**방법 1: 수동 다운로드 (추천)**

1. 링크 열기: https://drive.google.com/drive/folders/1Ghoy6w3BfHNgoRjj5jI9dX1BV0WyS8l_
2. `binance_30d.zip` 다운로드 (100 MB)
3. 파일 이동:
```powershell
Move-Item "$env:USERPROFILE\Downloads\binance_30d.zip" "D:\project\Fin-Hub\data\gekko-history\"
```
4. 압축 해제:
```powershell
cd D:\project\Fin-Hub\data\gekko-history
Expand-Archive binance_30d.zip -Force
```
5. 검증:
```bash
python scripts/gekko_data_integration.py
```

**방법 2: 자동 (실패 가능)**
```bash
python scripts/download_gekko_gdrive.py
```

---

## 5. 사용 예제

### 실시간 주가 조회

```python
from app.tools.unified_market_data import StockQuoteTool

tool = StockQuoteTool()
result = await tool.execute({"symbol": "TSLA"})
print(f"Tesla: ${result['price']:.2f} ({result['change_percent']:+.2f}%)")
```

### 암호화폐 가격 추적

```python
from app.tools.unified_market_data import CryptoPriceTool

tool = CryptoPriceTool()
btc = await tool.execute({"coin_id": "bitcoin"})
eth = await tool.execute({"coin_id": "ethereum"})

print(f"BTC: ${btc['price']:,.0f}")
print(f"ETH: ${eth['price']:,.2f}")
```

### 뉴스 감성 분석

```python
from app.tools.unified_market_data import FinancialNewsTool

tool = FinancialNewsTool()
result = await tool.execute({"query": "Federal Reserve", "page_size": 5})

for article in result['articles']:
    print(f"[{article['sentiment'].upper()}] {article['title']}")
```

### 경제 지표 대시보드

```python
from app.tools.unified_market_data import EconomicIndicatorTool

tool = EconomicIndicatorTool()
gdp = await tool.execute({"series_id": "GDP", "limit": 4})
unemployment = await tool.execute({"series_id": "UNRATE", "limit": 12})

print("GDP (Quarterly):", [obs['value'] for obs in gdp['observations']])
print("Unemployment (Monthly):", [obs['value'] for obs in unemployment['observations']])
```

### 역사 데이터 백테스팅

```python
import pandas as pd
import numpy as np

# AAPL 5년 데이터 로드
df = pd.read_csv("data/stock-data/AAPL.csv", index_col=0, parse_dates=True)

# 이동평균 전략
df['SMA_20'] = df['Close'].rolling(20).mean()
df['SMA_50'] = df['Close'].rolling(50).mean()

# 매수/매도 신호
df['signal'] = 0
df.loc[df['SMA_20'] > df['SMA_50'], 'signal'] = 1   # 골든 크로스
df.loc[df['SMA_20'] < df['SMA_50'], 'signal'] = -1  # 데드 크로스

# 수익률 계산
df['returns'] = df['Close'].pct_change()
df['strategy_returns'] = df['signal'].shift(1) * df['returns']

total_return = (1 + df['strategy_returns']).cumprod().iloc[-1] - 1
print(f"Total Return: {total_return*100:.2f}%")
```

### 종합 시장 모니터링

```python
from app.tools.unified_market_data import MarketOverviewTool

tool = MarketOverviewTool()
overview = await tool.execute({})

# 지수
for name, data in overview['indices'].items():
    if data:
        print(f"{name.upper()}: ${data['price']:.2f} ({data['change_percent']:+.2f}%)")

# 암호화폐
for name, data in overview['crypto'].items():
    if data:
        print(f"{name.upper()}: ${data['price']:,.2f} ({data['change_24h']:+.2f}%)")

# 최신 뉴스
for article in overview['news'][:3]:
    print(f"- {article['title']}")
```

---

## 📊 데이터 & API 요약표

| 데이터/API | 타입 | 크기 | 상태 | 사용 도구 |
|-----------|------|------|------|----------|
| S&P 500 주식 | 로컬 | 71 MB | ✅ | pandas 직접 |
| 암호화폐 캐시 | 로컬 | 365 KB | ⚠️ | (사용 안 함) |
| Gekko 데이터 | 로컬 | 0 MB | ⏳ | (선택) |
| Finnhub | API | - | ⚠️ | stock_quote (fallback) |
| Alpha Vantage | API | - | ✅ | stock_quote (메인) |
| MarketStack | API | - | 🔸 | stock_quote (backup) |
| CoinGecko | API | - | ✅ | crypto_price, overview |
| News API | API | - | ✅ | financial_news, overview |
| FRED | API | - | ✅ | economic_indicator, overview |
| OpenSanctions | API | - | ✅ | unified_data (sanctions) |

**범례:**
- ✅ 활성 사용 중
- ⚠️ 문제 있음 (fallback 작동)
- 🔸 대기 중 (fallback용)
- ⏳ 다운로드 필요

---

## 🎯 빠른 참조

### 테스트 스크립트
```bash
# API 전체 테스트
python scripts/test_all_apis.py

# Unified API 테스트
python scripts/test_unified_api.py

# Market Spoke 통합 테스트
python scripts/test_market_spoke_integration.py

# 데이터 검증
python scripts/validate_and_analyze_data.py
```

### 데이터 위치
```
D:\project\Fin-Hub\data\
├── stock-data\          (71 MB, 503 files)
├── crypto-cache\        (365 KB, 6 files)
├── gekko-history\       (0 MB, empty)
├── api_test_results.json
└── validation_report.json
```

### API 키 위치
```
D:\project\Fin-Hub\.env
```

---

**마지막 업데이트:** 2025-10-04
**테스트 상태:** 6/6 통과
**프로덕션 준비:** Market Spoke ✅
