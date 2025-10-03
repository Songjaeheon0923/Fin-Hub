# 🛠️ Market Spoke MCP 도구 사용 가이드

Claude Desktop에서 사용 가능한 13개 Market Spoke MCP 도구의 사용법입니다.

---

## 📋 목차
1. [기본 시장 데이터 도구 (7개)](#기본-시장-데이터-도구)
2. [고급 분석 도구 (6개)](#고급-분석-도구)

---

## 기본 시장 데이터 도구

### 1. 📊 Unified Market Data (통합 시장 데이터)
**설명**: 여러 데이터 소스에서 자동으로 폴백하여 포괄적인 시장 데이터 제공

**Claude Desktop 명령어:**
```
/mcp use fin-hub-market

AAPL의 주식 시세를 unified_market_data 도구로 조회해줘
```

**직접 사용 예시:**
```json
{
  "tool": "unified_market_data",
  "arguments": {
    "query_type": "stock_quote",
    "symbol": "AAPL"
  }
}
```

**주요 query_type:**
- `stock_quote` - 주식 시세
- `crypto_price` - 암호화폐 가격
- `news` - 금융 뉴스
- `economic` - 경제 지표
- `overview` - 시장 개요

**추가 예시:**

주식 시세:
```
/mcp use fin-hub-market
unified_market_data 도구로 AAPL 주식 시세를 조회해줘
```

뉴스 검색:
```
/mcp use fin-hub-market
unified_market_data 도구로 Tesla 관련 뉴스를 조회해줘
```

경제 지표:
```
/mcp use fin-hub-market
unified_market_data 도구로 GDP 경제 지표를 조회해줘
```

---

### 2. 💹 Stock Quote (주식 시세)
**설명**: 실시간 주식 시세 데이터 조회

**Claude Desktop 명령어:**
```
/mcp use fin-hub-market

TSLA의 현재 주가를 stock_quote 도구로 알려줘
```

**직접 사용 예시:**
```json
{
  "tool": "stock_quote",
  "arguments": {
    "symbol": "TSLA"
  }
}
```

**결과 포함 정보:**
- 현재가, 시가, 고가, 저가
- 거래량
- 변동률
- 데이터 소스

---

### 3. ₿ Crypto Price (암호화폐 가격)
**설명**: 암호화폐 가격 정보 조회

**Claude Desktop 명령어:**
```
/mcp use fin-hub-market

비트코인 현재 가격을 crypto_price 도구로 조회해줘
```

**직접 사용 예시:**
```json
{
  "tool": "crypto_price",
  "arguments": {
    "symbol": "BTC"
  }
}
```

**지원 암호화폐:**
- BTC (Bitcoin)
- ETH (Ethereum)
- 기타 주요 암호화폐

---

### 4. 📰 Financial News (금융 뉴스)
**설명**: 최신 금융 뉴스 조회

**Claude Desktop 명령어:**
```
/mcp use fin-hub-market

테슬라 관련 최신 뉴스를 financial_news 도구로 10개 가져와줘
```

**직접 사용 예시:**
```json
{
  "tool": "financial_news",
  "arguments": {
    "query": "Tesla earnings",
    "limit": 10
  }
}
```

**결과 포함 정보:**
- 뉴스 제목 및 설명
- 출처
- 발행 시간
- URL

---

### 5. 📈 Economic Indicator (경제 지표)
**설명**: 경제 지표 데이터 조회 (FRED API)

**Claude Desktop 명령어:**
```
/mcp use fin-hub-market

미국 GDP 데이터를 economic_indicator 도구로 조회해줘
```

**직접 사용 예시:**
```json
{
  "tool": "economic_indicator",
  "arguments": {
    "indicator": "GDP"
  }
}
```

**주요 지표:**
- GDP - 국내총생산
- CPI - 소비자물가지수
- UNRATE - 실업률

---

### 6. 🌍 Market Overview (시장 개요)
**설명**: 주요 지수를 포함한 종합 시장 개요

**Claude Desktop 명령어:**
```
/mcp use fin-hub-market

오늘 시장 전체 현황을 market_overview 도구로 보여줘
```

**직접 사용 예시:**
```json
{
  "tool": "market_overview",
  "arguments": {}
}
```

**결과 포함 정보:**
- S&P 500, NASDAQ, DOW 등 주요 지수
- 섹터별 성과
- 시장 동향

---

### 7. 🔍 API Status (API 상태)
**설명**: 모든 데이터 제공 API의 가용성 확인

**Claude Desktop 명령어:**
```
/mcp use fin-hub-market

현재 API 상태를 api_status 도구로 확인해줘
```

**직접 사용 예시:**
```json
{
  "tool": "api_status",
  "arguments": {}
}
```

**확인 가능한 API:**
- Finnhub
- Alpha Vantage
- NewsAPI
- CoinGecko
- FRED
- OpenSanctions
- MarketStack

---

## 고급 분석 도구

### 8. 📊 Technical Analysis (기술적 분석)
**설명**: RSI, MACD, Bollinger Bands 등 기술적 지표 분석

**Claude Desktop 명령어:**
```
/mcp use fin-hub-market

AAPL의 기술적 분석을 technical_analysis 도구로 해줘. 모든 지표를 30일 기준으로 분석해줘.
```

**직접 사용 예시:**
```json
{
  "tool": "technical_analysis",
  "arguments": {
    "symbol": "AAPL",
    "indicators": ["all"],
    "period": 30
  }
}
```

**지원 지표:**
- `rsi` - Relative Strength Index (과매수/과매도)
- `macd` - Moving Average Convergence Divergence (추세 전환)
- `bollinger` - Bollinger Bands (변동성)
- `sma` - Simple Moving Average (20/50/200일)
- `ema` - Exponential Moving Average (12/26/50일)
- `all` - 모든 지표

**결과 포함:**
- 각 지표의 현재 값
- 매매 신호 (BUY/SELL/NEUTRAL)
- 해석 가이드

---

### 9. 📉 Pattern Recognition (패턴 인식)
**설명**: 차트 패턴, 지지/저항선, 추세 분석

**Claude Desktop 명령어:**
```
/mcp use fin-hub-market

MSFT의 차트 패턴을 pattern_recognition 도구로 60일 기준으로 분석해줘
```

**직접 사용 예시:**
```json
{
  "tool": "pattern_recognition",
  "arguments": {
    "symbol": "MSFT",
    "patterns": ["all"],
    "period": 60
  }
}
```

**감지 가능한 패턴:**
- `trend` - 추세 분석 (상승/하락/횡보)
- `support_resistance` - 지지선/저항선
- `head_shoulders` - 헤드앤숄더 패턴
- `double_top_bottom` - 이중천정/이중바닥
- `triangle` - 삼각형 수렴 패턴
- `all` - 모든 패턴

**결과 포함:**
- 추세 방향 및 강도
- 주요 지지/저항 레벨
- 감지된 패턴과 신호

---

### 10. ⚠️ Anomaly Detection (이상 탐지)
**설명**: 통계적 방법으로 가격/거래량 이상 감지

**Claude Desktop 명령어:**
```
/mcp use fin-hub-market

TSLA의 이상 거래를 anomaly_detection 도구로 찾아줘. 민감도는 medium으로 90일 분석해줘.
```

**직접 사용 예시:**
```json
{
  "tool": "anomaly_detection",
  "arguments": {
    "symbol": "TSLA",
    "sensitivity": "medium",
    "period": 90
  }
}
```

**민감도 설정:**
- `low` - 낮은 민감도 (큰 이상만 감지)
- `medium` - 중간 민감도 (기본값)
- `high` - 높은 민감도 (작은 이상도 감지)

**감지 항목:**
- 가격 이상 (Z-Score)
- 거래량 스파이크
- 변동성 이상
- 가격 갭
- 범위 돌파

**결과 포함:**
- 이상 유형별 목록
- 심각도 등급 (HIGH/MEDIUM)
- 발생 날짜 및 상세 정보

---

### 11. 🔄 Stock Comparison (종목 비교)
**설명**: 여러 종목의 상관관계, 성과, 위험 비교

**Claude Desktop 명령어:**
```
/mcp use fin-hub-market

AAPL, MSFT, GOOGL 세 종목을 stock_comparison 도구로 90일 기준 비교해줘. 모든 지표를 분석해줘.
```

**직접 사용 예시:**
```json
{
  "tool": "stock_comparison",
  "arguments": {
    "symbols": ["AAPL", "MSFT", "GOOGL"],
    "period": 90,
    "metrics": ["all"]
  }
}
```

**비교 가능 지표:**
- `correlation` - 상관관계 분석
- `performance` - 수익률 비교
- `volatility` - 변동성 비교
- `risk_return` - 위험 조정 수익률
- `all` - 모든 지표

**제약:**
- 최소 2개, 최대 10개 종목

**결과 포함:**
- 종목 간 상관관계 매트릭스
- 성과 순위
- 변동성 비교
- 위험 조정 수익률

---

### 12. 😊 Sentiment Analysis (감성 분석)
**설명**: 뉴스 감성과 시장 데이터를 결합한 종합 감성 점수

**Claude Desktop 명령어:**
```
/mcp use fin-hub-market

NVDA의 시장 감성을 sentiment_analysis 도구로 최근 7일 분석해줘
```

**직접 사용 예시:**
```json
{
  "tool": "sentiment_analysis",
  "arguments": {
    "symbol": "NVDA",
    "query": "NVIDIA",
    "days": 7
  }
}
```

**분석 요소:**
- 뉴스 감성 (키워드 기반)
- 시장 모멘텀
- 종합 점수 (1-5 척도)

**결과 포함:**
- 종합 감성 점수 (1=매우 부정 ~ 5=매우 긍정)
- 감성 레이블 (VERY_POSITIVE, POSITIVE, NEUTRAL, NEGATIVE, VERY_NEGATIVE)
- 매수/매도 추천 (STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL)
- 뉴스 기사별 감성 분석
- 신뢰도 평가

---

### 13. 🔔 Alert System (알림 시스템)
**설명**: 가격 변동, 돌파, 패턴 감지를 위한 알림 생성

**Claude Desktop 명령어:**
```
/mcp use fin-hub-market

AMD에 대한 모든 알림을 alert_system 도구로 확인해줘. 5% 이상 변동과 거래량 2배 이상을 기준으로 해줘.
```

**직접 사용 예시:**
```json
{
  "tool": "alert_system",
  "arguments": {
    "symbol": "AMD",
    "alert_type": "all",
    "thresholds": {
      "percent_change": 5,
      "volume_multiplier": 2.0,
      "price_above": 150,
      "price_below": 100
    }
  }
}
```

**알림 유형:**
- `price_target` - 가격 목표 달성
- `percent_change` - 퍼센트 변화
- `volume_spike` - 거래량 급증
- `breakout` - 범위 돌파
- `support_resistance` - 지지/저항 근접
- `volatility` - 변동성 증가
- `all` - 모든 알림

**임계값 설정:**
- `price_above` - 이 가격 이상
- `price_below` - 이 가격 이하
- `percent_change` - 퍼센트 변화 (기본: 5%)
- `volume_multiplier` - 거래량 배수 (기본: 2.0)
- `volatility_threshold` - 변동성 배수 (기본: 1.5)

**결과 포함:**
- 활성 알림 목록
- 심각도 등급 (HIGH/MEDIUM)
- 알림 유형 및 상세 정보

---

## 💡 사용 팁

### 1. 도구 조합 활용
```
/mcp use fin-hub-market

AAPL을 분석해줘:
1. stock_quote로 현재 가격 확인
2. technical_analysis로 기술적 지표 분석
3. pattern_recognition으로 차트 패턴 확인
4. sentiment_analysis로 시장 감성 파악
```

### 2. 비교 분석
```
/mcp use fin-hub-market

기술주 빅3(AAPL, MSFT, GOOGL)를 stock_comparison으로 비교하고,
각각의 technical_analysis와 sentiment_analysis도 해줘
```

### 3. 리스크 모니터링
```
/mcp use fin-hub-market

내 포트폴리오 종목들(TSLA, NVDA, AMD)에 대해:
1. anomaly_detection으로 이상 거래 확인
2. alert_system으로 알림 설정
3. pattern_recognition으로 추세 확인
```

### 4. 시장 현황 파악
```
/mcp use fin-hub-market

오늘 시장 상황을 파악해줘:
1. market_overview로 전체 시장 현황
2. financial_news로 주요 뉴스
3. economic_indicator로 경제 지표
```

---

## 🔧 문제 해결

### MCP 서버가 보이지 않을 때
1. Claude Desktop 재시작
2. `claude_desktop_config.json` 확인
3. MCP 서버 프로세스 확인

### 도구 실행 오류
1. 심볼이 올바른지 확인 (대문자 사용)
2. S&P 500 종목인지 확인 (503개 종목 지원)
3. API 키가 설정되어 있는지 확인

### 데이터가 없을 때
- `api_status` 도구로 API 가용성 확인
- S&P 500 종목 리스트 확인: `data/stock-data/sp500_tickers.json`

---

## 📚 추가 리소스

- **전체 문서**: `docs/MCP_SERVERS_GUIDE.md`
- **테스트 스크립트**: `scripts/test_advanced_tools.py`
- **완료 기능**: `COMPLETED_FEATURES.md`
- **데이터 참조**: `docs/DATA_AND_API_REFERENCE.md`

---

**마지막 업데이트**: 2025-10-04
**Market Spoke 버전**: 1.0.0
**총 MCP 도구**: 13개 ✨
