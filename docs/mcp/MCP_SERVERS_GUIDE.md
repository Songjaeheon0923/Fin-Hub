# Fin-Hub MCP Servers 사용 가이드

이 문서는 Fin-Hub 프로젝트의 MCP 서버들과 각 서버가 제공하는 도구들의 사용법을 설명합니다.

## 목차
- [fin-hub-market](#fin-hub-market---시장-데이터-서버)
- [fin-hub-risk](#fin-hub-risk---리스크-관리-서버)
- [fin-hub-portfolio](#fin-hub-portfolio---포트폴리오-관리-서버)
- [fin-hub](#fin-hub---허브-관리-서버)

---

## fin-hub-market - 시장 데이터 서버

시장 데이터(주식, 암호화폐, 뉴스, 경제 지표 등)를 제공하는 서버입니다.

### 1. unified_market_data
**역할:** 여러 데이터 소스에서 포괄적인 시장 데이터를 가져오며, 자동 fallback 기능이 있습니다.

**파라미터:**
- `query_type` (필수): 데이터 타입 - "stock_quote", "crypto_price", "news", "economic", "overview" 중 하나
- `symbol`: 주식/암호화폐 심볼 (예: AAPL, BTC)
- `query`: 뉴스 검색 쿼리
- `indicator`: 경제 지표 코드 (예: GDP, CPI)

**시험 방법:**
```
통합 시장 데이터 도구를 사용해서 AAPL의 주식 시세를 가져와줘
```

### 2. stock_quote
**역할:** 실시간 주식 시세 데이터를 조회합니다.

**파라미터:**
- `symbol` (필수): 주식 티커 심볼 (예: AAPL, MSFT, GOOGL)

**시험 방법:**
```
AAPL 주식의 현재 시세를 알려줘
테슬라(TSLA) 주식 가격을 조회해줘
마이크로소프트 주식 정보를 보여줘
```

### 3. crypto_price
**역할:** 암호화폐 가격 데이터를 조회합니다.

**파라미터:**
- `symbol` (필수): 암호화폐 심볼 (예: BTC, ETH)

**시험 방법:**
```
비트코인 가격을 알려줘
이더리움(ETH) 현재 가격을 조회해줘
BTC 암호화폐 시세를 확인해줘
```

### 4. financial_news
**역할:** 최신 금융 뉴스를 검색합니다.

**파라미터:**
- `query` (필수): 뉴스 검색 쿼리 (예: 'Tesla earnings', 'Fed interest rates')
- `limit`: 반환할 뉴스 기사 수 (기본값: 10)

**시험 방법:**
```
테슬라 관련 최신 뉴스를 찾아줘
연준 금리 관련 뉴스 5개만 보여줘
애플 실적 발표 뉴스를 검색해줘
```

### 5. economic_indicator
**역할:** 경제 지표 데이터를 조회합니다.

**파라미터:**
- `indicator` (필수): 경제 지표 코드 (예: GDP, CPI, UNRATE)

**시험 방법:**
```
GDP 경제 지표 데이터를 보여줘
CPI(소비자물가지수) 데이터를 조회해줘
실업률(UNRATE) 지표를 확인해줘
```

### 6. market_overview
**역할:** 주요 지수를 포함한 종합 시장 개요를 제공합니다.

**파라미터:** 없음

**시험 방법:**
```
현재 시장 상황을 요약해줘
오늘 시장 개요를 보여줘
주요 지수 현황을 알려줘
```

### 7. api_status
**역할:** 모든 데이터 제공자 API의 상태와 가용성을 확인합니다.

**파라미터:** 없음

**시험 방법:**
```
market spoke API 상태를 확인해줘
데이터 제공자 API들이 정상 작동하는지 확인해줘
API 연결 상태를 점검해줘
```

---

## fin-hub-risk - 리스크 관리 서버

금융 데이터의 이상 탐지 및 컴플라이언스 검사를 수행하는 서버입니다.

### 1. detect_anomaly
**역할:** 금융 데이터에서 이상치(anomaly)를 탐지합니다.

**파라미터:**
- `data` (필수): 분석할 숫자 데이터 포인트 배열
- `threshold`: 이상 탐지 민감도 임계값 (기본값: 2.0)

**시험 방법:**
```
다음 데이터에서 이상치를 탐지해줘: [10, 12, 11, 13, 100, 12, 11]
데이터 [50, 52, 51, 53, 200, 52]에서 이상치를 찾아줘 (임계값 1.5 사용)
주식 가격 데이터 [100, 102, 101, 103, 105, 500, 104]의 이상치를 분석해줘
```

### 2. check_compliance
**역할:** 포트폴리오가 규정을 준수하는지 확인합니다.

**파라미터:**
- `portfolio` (필수): 확인할 포트폴리오 보유 내역
- `rules`: 확인할 컴플라이언스 규칙 배열

**시험 방법:**
```
내 포트폴리오 {"AAPL": 100, "GOOGL": 50}의 컴플라이언스를 확인해줘
포트폴리오 준수 여부를 검사해줘
```

---

## fin-hub-portfolio - 포트폴리오 관리 서버

포트폴리오 최적화, 리밸런싱, 성과 분석을 수행하는 서버입니다.

### 1. optimize_portfolio
**역할:** 리스크/수익 선호도에 따라 최적의 포트폴리오 배분을 생성합니다.

**파라미터:**
- `assets` (필수): 자산 목록 (각 자산은 symbol, expected_return, risk 포함)
- `risk_tolerance`: 리스크 허용 수준 - "conservative", "moderate", "aggressive" (기본값: "moderate")
- `total_amount`: 투자 총액 (기본값: 10000)

**시험 방법:**
```
다음 자산들로 포트폴리오를 최적화해줘:
[
  {"symbol": "AAPL", "expected_return": 0.12, "risk": 0.15},
  {"symbol": "GOOGL", "expected_return": 0.15, "risk": 0.20},
  {"symbol": "MSFT", "expected_return": 0.10, "risk": 0.12}
]
위험 허용도는 conservative로 설정하고 총 투자금은 50000

공격적인(aggressive) 리스크로 $100,000 포트폴리오를 최적화해줘
```

### 2. rebalance_portfolio
**역할:** 목표 배분에 맞추기 위해 필요한 리밸런싱 작업을 계산합니다.

**파라미터:**
- `current_holdings` (필수): 현재 포트폴리오 보유량 {symbol: quantity}
- `target_allocation` (필수): 목표 배분 비율 {symbol: percentage}
- `current_prices` (필수): 현재 시장 가격 {symbol: price}

**시험 방법:**
```
포트폴리오 리밸런싱을 계산해줘:
- 현재 보유: {"AAPL": 10, "GOOGL": 5, "MSFT": 8}
- 목표 배분: {"AAPL": 0.4, "GOOGL": 0.3, "MSFT": 0.3}
- 현재 가격: {"AAPL": 150, "GOOGL": 140, "MSFT": 350}

내 포트폴리오를 리밸런싱하려면 어떻게 해야 하는지 알려줘
```

### 3. analyze_performance
**역할:** 포트폴리오 성과 지표를 분석합니다.

**파라미터:**
- `holdings` (필수): 포트폴리오 보유 내역 {symbol: {quantity, purchase_price}}
- `current_prices` (필수): 현재 시장 가격 {symbol: price}

**시험 방법:**
```
포트폴리오 성과를 분석해줘:
- 보유 내역: {
    "AAPL": {"quantity": 10, "purchase_price": 120},
    "GOOGL": {"quantity": 5, "purchase_price": 100}
  }
- 현재 가격: {"AAPL": 150, "GOOGL": 140}

내 포트폴리오의 수익률을 계산해줘
각 종목별 손익을 분석해줘
```

---

## fin-hub - 허브 관리 서버

Fin-Hub 시스템의 전체 상태를 관리하는 중앙 서버입니다.

### 1. hub_status
**역할:** 허브 서버 상태 및 등록된 spoke 서비스를 확인합니다.

**파라미터:** 없음

**시험 방법:**
```
허브 서버 상태를 확인해줘
Fin-Hub 시스템 상태를 보여줘
```

### 2. list_spokes
**역할:** 등록된 모든 spoke 서비스를 나열합니다.

**파라미터:** 없음

**시험 방법:**
```
등록된 spoke 서비스 목록을 보여줘
연결된 서비스들을 알려줘
```

---

## 종합 테스트 시나리오

### 시나리오 1: 주식 분석 및 포트폴리오 최적화
```
1. AAPL, GOOGL, MSFT 주식 시세를 각각 조회해줘
2. 이 세 종목으로 moderate 리스크의 포트폴리오를 최적화해줘 (총 $50,000)
3. 최적화된 포트폴리오의 성과를 분석해줘
```

### 시나리오 2: 시장 모니터링 및 뉴스 추적
```
1. 현재 시장 개요를 보여줘
2. 테슬라 관련 최신 뉴스 5개를 찾아줘
3. GDP 경제 지표를 확인해줘
```

### 시나리오 3: 리스크 관리
```
1. 내 포트폴리오 데이터 [100, 102, 105, 103, 500, 104]에서 이상치를 탐지해줘
2. 포트폴리오 컴플라이언스를 확인해줘
3. 리밸런싱이 필요한지 계산해줘
```

### 시나리오 4: 암호화폐 모니터링
```
1. 비트코인과 이더리움 가격을 조회해줘
2. 암호화폐 관련 최신 뉴스를 찾아줘
3. API 상태를 확인해줘
```

---

## 주의사항

1. **API 키 필요:** market-spoke 서버는 여러 외부 API를 사용하므로, 해당 API 키들이 환경변수로 설정되어 있어야 합니다.

2. **네트워크 연결:** 실시간 데이터를 가져오므로 인터넷 연결이 필요합니다.

3. **데이터 정확성:** 제공되는 데이터는 외부 API에서 가져오므로, 각 API의 한계와 정확성에 따라 달라질 수 있습니다.

4. **Rate Limiting:** 일부 API는 요청 제한이 있을 수 있습니다. 과도한 요청은 피해주세요.

---

## 문제 해결

### MCP 서버가 연결되지 않을 때
1. Claude Desktop을 완전히 종료하고 재시작
2. 로그 파일 확인: `C:\Users\<username>\AppData\Roaming\Claude\logs\mcp-server-*.log`
3. Python 및 필요한 패키지가 설치되어 있는지 확인

### 도구 실행이 실패할 때
1. API 키가 올바르게 설정되어 있는지 확인
2. 네트워크 연결 상태 확인
3. 입력 파라미터 형식이 올바른지 확인

---

## 추가 정보

- **프로젝트 문서:** `docs/README.md`
- **API 레퍼런스:** `docs/DATA_AND_API_REFERENCE.md`
- **설정 파일:** `C:\Users\<username>\AppData\Roaming\Claude\claude_desktop_config.json`
