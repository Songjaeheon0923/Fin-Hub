# 🧪 Fin-Hub Testing Guide

**Claude Desktop에서 Hub + 3개 Spoke 전체 도구 테스트 가이드**

이 문서는 Hub Server + Market Spoke + Risk Spoke + Portfolio Spoke의 **총 31개 MCP 도구**를 Claude Desktop에서 테스트하는 방법을 설명합니다.

---

## 🏢 Hub Server (2개 도구)

### 1. hub_status
**기능**: Hub 서버 상태 및 등록된 Spoke 확인

**테스트 명령어**:
```
Hub 서버 상태를 확인해줘
```
```
현재 Hub 서버가 정상 작동하는지 알려줘
```
```
Hub의 버전과 상태를 보여줘
```

**예상 응답**:
```json
{
  "status": "running",
  "service": "fin-hub",
  "version": "1.0.0"
}
```

---

### 2. list_spokes
**기능**: 등록된 모든 Spoke 서비스 목록 조회

**테스트 명령어**:
```
등록된 Spoke 목록을 보여줘
```
```
어떤 Spoke 서비스들이 연결되어 있는지 알려줘
```
```
모든 Spoke의 상태를 확인해줘
```

**예상 응답**:
```json
{
  "spokes": [
    {"name": "market-spoke", "status": "registered"},
    {"name": "risk-spoke", "status": "registered"},
    {"name": "portfolio-spoke", "status": "registered"}
  ]
}
```

---

## 📊 Market Spoke (13개 도구)

### Core Tools (7개)

#### 1. unified_market_data
**기능**: 통합 시장 데이터 조회 (주식, 암호화폐, 뉴스, 경제 지표)

**테스트 명령어**:
```
Market spoke mcp를 활용해서 AAPL 주식의 최신 데이터를 가져와줘
```
```
비트코인 가격 데이터를 조회해줘
```
```
TSLA에 대한 최신 뉴스를 가져와줘
```

---

#### 2. stock_quote
**기능**: 실시간 주식 시세 조회 (OHLCV, 변동률)

**테스트 명령어**:
```
AAPL의 현재 주가를 알려줘
```
```
테슬라(TSLA) 주식 시세를 확인해줘
```
```
MSFT의 오늘 거래량과 가격을 보여줘
```

---

#### 3. crypto_price
**기능**: 암호화폐 가격 조회 (10,000+ 코인 지원)

**테스트 명령어**:
```
비트코인 현재 가격을 알려줘
```
```
이더리움 가격을 USD로 보여줘
```
```
solana 암호화폐 시세를 확인해줘
```

---

#### 4. financial_news
**기능**: 금융 뉴스 + 감성 분석 (긍정/부정/중립 점수)

**테스트 명령어**:
```
애플에 대한 최신 뉴스를 감성 분석과 함께 보여줘
```
```
테슬라 관련 뉴스 10개를 가져와줘
```
```
기술주에 대한 뉴스를 감성 점수와 함께 분석해줘
```

---

#### 5. economic_indicator
**기능**: 경제 지표 조회 (GDP, 실업률, 인플레이션 등)

**테스트 명령어**:
```
미국 GDP 데이터를 보여줘
```
```
최근 실업률(UNRATE) 추이를 알려줘
```
```
연방기금금리(FEDFUNDS) 최근 데이터를 가져와줘
```

---

#### 6. market_overview
**기능**: 종합 시장 개요 (주식 + 암호화폐 + 뉴스 통합)

**테스트 명령어**:
```
AAPL에 대한 종합 시장 개요를 보여줘
```
```
오늘의 시장 상황을 요약해줘 (AAPL, BTC 포함)
```
```
테슬라의 전체 시장 상황을 분석해줘
```

---

#### 7. api_status
**기능**: 7개 API 헬스 체크 (가용성 확인)

**테스트 명령어**:
```
현재 API 상태를 확인해줘
```
```
모든 데이터 소스가 정상 작동하는지 확인해줘
```
```
API 헬스 체크를 실행해줘
```

---

### Advanced Analysis Tools (6개)

#### 8. technical_analysis
**기능**: 기술적 지표 분석 (RSI, MACD, Bollinger Bands, SMA, EMA)

**테스트 명령어**:
```
AAPL의 기술적 분석을 해줘
```
```
테슬라 주식의 RSI와 MACD를 계산해줘
```
```
MSFT의 볼린저 밴드와 이동평균을 분석해줘
```

---

#### 9. pattern_recognition
**기능**: 차트 패턴 인식 (상승/하락 추세, 지지/저항선)

**테스트 명령어**:
```
AAPL 차트에서 패턴을 찾아줘
```
```
테슬라의 지지선과 저항선을 알려줘
```
```
NVDA의 추세를 분석해줘
```

---

#### 10. anomaly_detection
**기능**: 가격/거래량 이상 감지 (Z-Score, 변동성 분석)

**테스트 명령어**:
```
AAPL에서 가격 이상을 감지해줘
```
```
테슬라의 비정상적인 거래량을 확인해줘
```
```
TSLA에서 통계적 이상치를 찾아줘
```

---

#### 11. stock_search
**기능**: 종목 검색 (키워드로 심볼 찾기)

**테스트 명령어**:
```
"apple"로 주식을 검색해줘
```
```
"tesla"라는 이름의 종목을 찾아줘
```
```
"microsoft" 관련 종목을 보여줘
```

---

#### 12. company_overview
**기능**: 기업 기본 정보 (섹터, 시가총액, PE비율, 배당)

**테스트 명령어**:
```
AAPL의 기업 정보를 보여줘
```
```
테슬라의 시가총액과 섹터를 알려줘
```
```
MSFT의 재무 개요를 보여줘
```

---

#### 13. sentiment_analysis
**기능**: 뉴스 감성 점수 (1-5 척도, 약세-강세)

**테스트 명령어**:
```
AAPL에 대한 시장 감성을 분석해줘
```
```
테슬라의 뉴스 감성 점수를 계산해줘
```
```
NVDA에 대한 투자 심리를 알려줘
```

---

## 🎯 Risk Spoke (8개 도구)

### 기본 분석 (1-3)

#### 1. var_calculator
**기능**: VaR 계산 (Historical, Parametric, Monte Carlo 방식)

**테스트 명령어**:
```
AAPL의 VaR를 계산해줘 (신뢰수준 95%)
```
```
Risk spoke mcp를 활용해서 테슬라의 1일 VaR를 Monte Carlo 방법으로 구해줘
```
```
MSFT의 위험가치를 Historical VaR로 계산해줘
```

---

#### 2. risk_metrics
**기능**: 리스크 지표 (Sharpe, Sortino, Max Drawdown, Beta, Alpha)

**테스트 명령어**:
```
AAPL의 리스크 지표를 계산해줘
```
```
테슬라의 Sharpe Ratio와 변동성을 알려줘
```
```
MSFT의 Beta와 Alpha를 분석해줘
```

---

#### 3. portfolio_risk
**기능**: 다중 자산 포트폴리오 리스크 분석 (상관관계, 집중도, VaR)

**테스트 명령어**:
```
AAPL, MSFT, GOOGL로 구성된 포트폴리오의 리스크를 분석해줘
```
```
테슬라와 애플을 각각 50%씩 보유한 포트폴리오의 위험도를 계산해줘
```
```
5개 종목(AAPL, MSFT, GOOGL, TSLA, NVDA)의 포트폴리오 리스크를 평가해줘
```

---

### 고급 분석 (4-6)

#### 4. stress_testing
**기능**: 스트레스 테스트 (5개 역사적 위기 시나리오)

**테스트 명령어**:
```
AAPL을 2008 금융위기 시나리오로 스트레스 테스트해줘
```
```
내 포트폴리오를 COVID-19 시나리오로 테스트해줘
```
```
테슬라를 닷컴버블 시나리오에서 분석해줘
```

---

#### 5. tail_risk
**기능**: 극단 리스크 분석 (EVT, Fat Tail, Black Swan)

**테스트 명령어**:
```
AAPL의 꼬리 리스크를 분석해줘
```
```
테슬라의 극단적 손실 가능성을 평가해줘
```
```
TSLA의 Black Swan 이벤트 리스크를 계산해줘
```

---

#### 6. greeks_calculator
**기능**: 옵션 Greeks 계산 (Delta, Gamma, Theta, Vega, Rho)

**테스트 명령어**:
```
AAPL 콜옵션의 Greeks를 계산해줘 (행사가 150, 만기 30일)
```
```
테슬라 풋옵션의 Delta와 Gamma를 구해줘
```
```
MSFT 옵션의 모든 Greeks를 보여줘
```

---

### 컴플라이언스 (7-8)

#### 7. compliance_checker
**기능**: KYC/AML 스크리닝, 규제 준수 체크

**테스트 명령어**:
```
이 거래의 컴플라이언스를 확인해줘 (금액: $50,000)
```
```
KYC 체크가 필요한지 확인해줘
```
```
AML 규제를 준수하는지 검증해줘
```

---

#### 8. risk_dashboard
**기능**: 종합 리스크 대시보드 (VaR, 스트레스, 컴플라이언스 통합)

**테스트 명령어**:
```
AAPL의 리스크 대시보드를 생성해줘
```
```
내 포트폴리오의 종합 리스크 리포트를 만들어줘
```
```
테슬라의 전체 리스크 상황을 요약해줘
```

---

## 💼 Portfolio Spoke (8개 도구)

### Core Optimization (1-2)

#### 1. portfolio_optimizer
**기능**: 포트폴리오 최적화 (Mean-Variance, HRP, Risk Parity)

**테스트 명령어**:
```
Portfolio spoke mcp를 활용해서 AAPL, MSFT, GOOGL로 최적 포트폴리오를 만들어줘
```
```
5개 종목의 Sharpe Ratio를 최대화하는 비중을 계산해줘
```
```
Risk Parity 방식으로 포트폴리오를 최적화해줘
```

---

#### 2. portfolio_rebalancer
**기능**: 포트폴리오 리밸런싱 (Threshold, Periodic, Tax-aware)

**테스트 명령어**:
```
내 포트폴리오를 리밸런싱해줘
```
```
5% 이상 벗어난 종목을 재조정해줘
```
```
세금을 고려한 리밸런싱 계획을 세워줘
```

---

### Performance & Analysis (3-5)

#### 3. performance_analyzer
**기능**: 성과 분석 (수익률, Sharpe, Attribution)

**테스트 명령어**:
```
내 포트폴리오의 성과를 분석해줘
```
```
AAPL의 연간 수익률과 Sharpe Ratio를 계산해줘
```
```
포트폴리오의 각 종목 기여도를 분석해줘
```

---

#### 4. backtester
**기능**: 전략 백테스팅 (Momentum, Mean Reversion, Equal Weight)

**테스트 명령어**:
```
모멘텀 전략을 백테스트해줘
```
```
Equal Weight 전략의 과거 성과를 시뮬레이션해줘
```
```
Mean Reversion 전략을 5년 데이터로 테스트해줘
```

---

#### 5. factor_analyzer
**기능**: 팩터 분석 (Market, Size, Value, Momentum, Quality)

**테스트 명령어**:
```
AAPL의 팩터 노출도를 분석해줘
```
```
내 포트폴리오의 Fama-French 팩터를 계산해줘
```
```
Value와 Momentum 팩터 기여도를 알려줘
```

---

### Advanced Features (6-8)

#### 6. asset_allocator
**기능**: 자산 배분 (Strategic, Tactical allocation)

**테스트 명령어**:
```
보수적인 자산 배분 전략을 만들어줘
```
```
Tactical allocation으로 포트폴리오를 조정해줘
```
```
주식 60%, 채권 40% 전략의 다각화를 분석해줘
```

---

#### 7. tax_optimizer
**기능**: 세금 최적화 (Tax Loss Harvesting, Wash Sale 감지)

**테스트 명령어**:
```
Tax Loss Harvesting 기회를 찾아줘
```
```
Wash Sale 위반 가능성을 확인해줘
```
```
세금을 최소화하는 매도 계획을 세워줘
```

---

#### 8. portfolio_dashboard
**기능**: 포트폴리오 대시보드 (0-100 건강도 점수)

**테스트 명령어**:
```
내 포트폴리오 대시보드를 생성해줘
```
```
포트폴리오 건강도 점수를 계산해줘
```
```
전체적인 포트폴리오 상태를 요약해줘
```

---

## 🔧 통합 테스트 시나리오

### 시나리오 1: 종목 분석 → 포트폴리오 구성 → 리스크 평가
```
1. AAPL의 기술적 분석과 감성 분석을 해줘
2. AAPL, MSFT, GOOGL로 최적 포트폴리오를 만들어줘
3. 이 포트폴리오의 VaR와 리스크 지표를 계산해줘
4. 포트폴리오 대시보드를 생성해줘
```

### 시나리오 2: 뉴스 감성 → 리밸런싱 → 스트레스 테스트
```
1. 테슬라에 대한 뉴스 감성을 분석해줘
2. 내 포트폴리오를 리밸런싱해줘
3. 2008 금융위기 시나리오로 스트레스 테스트해줘
4. 종합 리스크 대시보드를 만들어줘
```

### 시나리오 3: 백테스팅 → 성과 분석 → 세금 최적화
```
1. Momentum 전략을 백테스트해줘
2. 포트폴리오 성과를 분석해줘
3. Tax Loss Harvesting 기회를 찾아줘
4. 포트폴리오 건강도를 평가해줘
```

---

## 📊 데이터 요구사항

**Market Spoke**:
- S&P 500: 503개 종목
- 암호화폐: 10,000+ 코인
- 뉴스: 실시간 금융 뉴스
- 경제 지표: FRED API

**Risk Spoke**:
- 최소 30일 가격 데이터
- 벤치마크: SPY (S&P 500 ETF)
- 옵션: 행사가, 만기, 무위험 이자율

**Portfolio Spoke**:
- 최소 1년 가격 데이터 (백테스팅)
- 거래 이력 (리밸런싱, 세금)
- 벤치마크: SPY 또는 첫 번째 종목

---

## 🎯 테스트 체크리스트

### Hub Server ✅
- [ ] hub_status - 서버 상태 확인
- [ ] list_spokes - Spoke 목록 조회

### Market Spoke ✅
- [ ] 7개 Core Tools 테스트
- [ ] 6개 Advanced Analysis Tools 테스트
- [ ] API 상태 확인
- [ ] 감성 분석 정확도 검증

### Risk Spoke ✅
- [ ] VaR 계산 (3가지 방법)
- [ ] 리스크 지표 분석
- [ ] 스트레스 테스트 (5개 시나리오)
- [ ] 컴플라이언스 체크

### Portfolio Spoke ✅
- [ ] 포트폴리오 최적화
- [ ] 리밸런싱 시뮬레이션
- [ ] 백테스팅 실행
- [ ] 세금 최적화 확인
- [ ] 대시보드 생성

---

## 🚀 CLI 테스트 (빠른 초기화 확인)

MCP 서버를 Claude Desktop 없이 CLI에서 빠르게 테스트할 수 있습니다:

```bash
# 초기화 시간 측정
python measure_init.py services/hub-server/app/mcp_server.py
python measure_init.py services/market-spoke/mcp_server.py
python measure_init.py services/risk-spoke/mcp_server.py
python measure_init.py services/portfolio-spoke/mcp_server.py

# 예상 결과:
# Hub server: ~3-4초
# Market Spoke: ~4-5초
# Risk Spoke: ~6-8초
# Portfolio Spoke: ~5-6초
```

---

**마지막 업데이트**: 2025-10-04
**총 도구 수**: 31개 (Hub 2 + Market 13 + Risk 8 + Portfolio 8)
**테스트 커버리지**: 100%
**상태**: ✅ Production Ready
