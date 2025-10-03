# Fin-Hub Documentation

**최고 수준의 금융 데이터 허브 - 전문 문서 센터**

---

## 📁 문서 구조

```
docs/
├── README.md                           ← 현재 파일 (문서 인덱스)
├── market-spoke/                       ← Market Spoke (시장 데이터)
│   ├── MARKET_SPOKE_DESIGN.md
│   ├── MARKET_SPOKE_USAGE.md
│   └── MARKET_SPOKE_API_REFERENCE.md
├── risk-spoke/                         ← Risk Spoke (리스크 관리)
│   ├── RISK_SPOKE_DESIGN.md
│   └── RISK_SPOKE_USAGE.md
├── portfolio-spoke/                    ← Portfolio Spoke (포트폴리오 관리)
│   ├── PORTFOLIO_SPOKE_DESIGN.md
│   ├── PORTFOLIO_SPOKE_USAGE.md
│   └── PORTFOLIO_SPOKE_RESEARCH.md
└── archive/                            ← 구버전/참고용
```

---

## 🚀 빠른 시작

### Market Spoke 사용하기
→ **[market-spoke/MARKET_SPOKE_USAGE.md](market-spoke/MARKET_SPOKE_USAGE.md)**
- 13개 시장 데이터 도구 사용법
- 주식, 암호화폐, 뉴스, 거시경제 데이터
- 실전 예제 및 API 매핑

### Risk Spoke 사용하기
→ **[risk-spoke/RISK_SPOKE_USAGE.md](risk-spoke/RISK_SPOKE_USAGE.md)**
- 8개 전문 리스크 관리 도구
- VaR, Stress Testing, Greeks, Compliance 등
- 종합 리스크 대시보드

### Portfolio Spoke 사용하기
→ **[portfolio-spoke/PORTFOLIO_SPOKE_USAGE.md](portfolio-spoke/PORTFOLIO_SPOKE_USAGE.md)**
- 8개 포트폴리오 관리 도구
- 최적화, 리밸런싱, 성과 분석, 백테스팅
- 자산 배분, 세금 최적화, 대시보드

---

## 📊 Market Spoke (시장 데이터)

### [MARKET_SPOKE_DESIGN.md](market-spoke/MARKET_SPOKE_DESIGN.md)
**Market Spoke 아키텍처 및 설계 문서**

**포함 내용:**
- 시스템 아키텍처 (MCP Server + API Manager + Cache)
- 13개 도구 상세 설계
- API 통합 전략 (7개 API)
- 캐싱 및 성능 최적화
- 보안 및 신뢰성

**대상:** 아키텍트, 시니어 개발자

---

### [MARKET_SPOKE_USAGE.md](market-spoke/MARKET_SPOKE_USAGE.md)
**13개 MCP 도구 완전 가이드**

**도구 카테고리:**
1. **Core Tools (7개)**
   - unified_market_data, stock_quote, crypto_price
   - financial_news, economic_indicator
   - market_overview, api_status

2. **Advanced Analysis (6개)**
   - technical_analysis, pattern_recognition
   - anomaly_detection, stock_search
   - company_overview, sentiment_analysis

**테스트:** 100% 통과
**Status:** ✅ Production Ready

---

### [MARKET_SPOKE_API_REFERENCE.md](market-spoke/MARKET_SPOKE_API_REFERENCE.md)
**데이터셋 및 API 완전 참조**

**포함 내용:**
- 📦 로컬 데이터셋 (S&P 500: 503 stocks)
- 🔌 7개 외부 API (Finnhub, Alpha Vantage, MarketStack, CoinGecko, News API, FRED, Polygon)
- 🗺️ MCP 도구 ↔ API 매핑
- 📥 다운로드 가이드
- 💡 사용 예제

**대상:** 개발자, 데이터 분석가

---

## 🎯 Risk Spoke (리스크 관리)

### [RISK_SPOKE_DESIGN.md](risk-spoke/RISK_SPOKE_DESIGN.md)
**Risk Spoke 아키텍처 및 설계 문서**

**포함 내용:**
- 시스템 아키텍처
- 8개 도구별 상세 설계
- 리스크 방법론 및 알고리즘
- 데이터 플로우
- 규제 준수 (Basel III, DORA, SR 21-14)

**대상:** 아키텍트, 리스크 관리자

---

### [RISK_SPOKE_USAGE.md](risk-spoke/RISK_SPOKE_USAGE.md)
**8개 전문 리스크 도구 종합 가이드**

**도구 목록:**

**기본 분석 (1-3)**
1. VaR Calculator - Value at Risk (Historical, Parametric, Monte Carlo)
2. Risk Metrics - Sharpe, Sortino, Drawdown, Beta, Alpha 등
3. Portfolio Risk - 다중 자산 포트폴리오 분석

**고급 분석 (4-6)**
4. Stress Testing - 5개 역사적 위기 시나리오
5. Tail Risk Analyzer - EVT, Fat Tail, Black Swan 분석
6. Greeks Calculator - Black-Scholes 옵션 Greeks

**컴플라이언스 (7-8)**
7. Compliance Checker - KYC/AML 스크리닝, 규제 준수
8. Risk Dashboard - 종합 리스크 대시보드

**테스트:** 17/17 통과 (100%)
**코드:** ~4,453 lines

---

## 💼 Portfolio Spoke (포트폴리오 관리)

### [PORTFOLIO_SPOKE_DESIGN.md](portfolio-spoke/PORTFOLIO_SPOKE_DESIGN.md)
**Portfolio Spoke 아키텍처 및 설계 문서**

**포함 내용:**
- 시스템 아키텍처
- 8개 도구별 상세 설계
- 포트폴리오 최적화 알고리즘
- 세금 최적화 전략
- 통합 전략

**대상:** 아키텍트, 포트폴리오 매니저

---

### [PORTFOLIO_SPOKE_USAGE.md](portfolio-spoke/PORTFOLIO_SPOKE_USAGE.md)
**8개 포트폴리오 관리 도구 완전 가이드**

**도구 목록:**

**Core Optimization (1-2)**
1. Portfolio Optimizer - Mean-Variance, HRP, Risk Parity
2. Portfolio Rebalancer - Threshold, Periodic, Tax-aware

**Performance & Analysis (3-5)**
3. Performance Analyzer - Returns, Sharpe, Attribution
4. Backtester - Momentum, Mean Reversion, Equal Weight
5. Factor Analyzer - Market, Size, Value, Momentum, Quality

**Advanced Features (6-8)**
6. Asset Allocator - Strategic/Tactical allocation
7. Tax Optimizer - Tax Loss Harvesting, Wash Sale detection
8. Portfolio Dashboard - Health scoring (0-100)

**테스트:** 12/12 통과 (100%)
**코드:** ~4,800 lines

---

### [PORTFOLIO_SPOKE_RESEARCH.md](portfolio-spoke/PORTFOLIO_SPOKE_RESEARCH.md)
**Portfolio Spoke 연구 및 참고 자료**

**포함 내용:**
- 포트폴리오 최적화 이론
- 학술 연구 참조
- 라이브러리 비교
- 구현 선택 근거

**대상:** 연구자, 퀀트 개발자

---

## 🔧 MCP 통합

### [MCP_SERVERS_GUIDE.md](mcp/MCP_SERVERS_GUIDE.md)
**MCP 서버 설정 및 관리 가이드**

**포함 내용:**
- MCP 프로토콜 개요
- 서버 설치 방법
- Claude Desktop 설정
- 개발 및 디버깅
- 트러블슈팅

**서버 목록:**
- `fin-hub-market` - Market Spoke (13 tools)
- `fin-hub-risk` - Risk Spoke (8 tools)
- `fin-hub-portfolio` - Portfolio Spoke (8 tools)

**대상:** DevOps, 시스템 관리자

---

## 📖 권장 읽기 순서

### 처음 시작하는 경우
1. **프로젝트 개요** → [../COMPLETED_FEATURES.md](../COMPLETED_FEATURES.md)
2. **Market Spoke 사용** → [market-spoke/MARKET_SPOKE_USAGE.md](market-spoke/MARKET_SPOKE_USAGE.md)
3. **MCP 설정** → [mcp/MCP_SERVERS_GUIDE.md](mcp/MCP_SERVERS_GUIDE.md)

### 시장 데이터 분석
1. **도구 사용법** → [market-spoke/MARKET_SPOKE_USAGE.md](market-spoke/MARKET_SPOKE_USAGE.md)
2. **설계 문서** → [market-spoke/MARKET_SPOKE_DESIGN.md](market-spoke/MARKET_SPOKE_DESIGN.md)
3. **데이터 참조** → [market-spoke/MARKET_SPOKE_API_REFERENCE.md](market-spoke/MARKET_SPOKE_API_REFERENCE.md)

### 리스크 관리
1. **도구 가이드** → [risk-spoke/RISK_SPOKE_USAGE.md](risk-spoke/RISK_SPOKE_USAGE.md)
2. **설계 문서** → [risk-spoke/RISK_SPOKE_DESIGN.md](risk-spoke/RISK_SPOKE_DESIGN.md)

### 포트폴리오 관리
1. **도구 가이드** → [portfolio-spoke/PORTFOLIO_SPOKE_USAGE.md](portfolio-spoke/PORTFOLIO_SPOKE_USAGE.md)
2. **설계 문서** → [portfolio-spoke/PORTFOLIO_SPOKE_DESIGN.md](portfolio-spoke/PORTFOLIO_SPOKE_DESIGN.md)
3. **연구 자료** → [portfolio-spoke/PORTFOLIO_SPOKE_RESEARCH.md](portfolio-spoke/PORTFOLIO_SPOKE_RESEARCH.md)

### 시스템 통합
1. **MCP 서버** → [mcp/MCP_SERVERS_GUIDE.md](mcp/MCP_SERVERS_GUIDE.md)
2. **API 참조** → [market-spoke/MARKET_SPOKE_API_REFERENCE.md](market-spoke/MARKET_SPOKE_API_REFERENCE.md)

---

## 🎯 빠른 참조

| 필요한 정보 | 문서 위치 |
|------------|----------|
| Market Spoke 도구 사용법 | [market-spoke/MARKET_SPOKE_USAGE.md](market-spoke/MARKET_SPOKE_USAGE.md) |
| Market Spoke 설계 | [market-spoke/MARKET_SPOKE_DESIGN.md](market-spoke/MARKET_SPOKE_DESIGN.md) |
| Risk Spoke 도구 사용법 | [risk-spoke/RISK_SPOKE_USAGE.md](risk-spoke/RISK_SPOKE_USAGE.md) |
| Risk Spoke 설계 | [risk-spoke/RISK_SPOKE_DESIGN.md](risk-spoke/RISK_SPOKE_DESIGN.md) |
| Portfolio Spoke 도구 사용법 | [portfolio-spoke/PORTFOLIO_SPOKE_USAGE.md](portfolio-spoke/PORTFOLIO_SPOKE_USAGE.md) |
| Portfolio Spoke 설계 | [portfolio-spoke/PORTFOLIO_SPOKE_DESIGN.md](portfolio-spoke/PORTFOLIO_SPOKE_DESIGN.md) |
| 데이터셋 및 API 정보 | [market-spoke/MARKET_SPOKE_API_REFERENCE.md](market-spoke/MARKET_SPOKE_API_REFERENCE.md) |
| MCP 서버 설정 | [mcp/MCP_SERVERS_GUIDE.md](mcp/MCP_SERVERS_GUIDE.md) |
| 프로젝트 상태 | [../COMPLETED_FEATURES.md](../COMPLETED_FEATURES.md) |
| 향후 계획 | [../PENDING_TASKS.md](../PENDING_TASKS.md) |

---

## 📊 프로젝트 통계

**Market Spoke:**
- 13개 MCP 도구
- 7개 외부 API 통합
- 503개 S&P 500 종목
- 100% 테스트 통과

**Risk Spoke:**
- 8개 전문 리스크 도구
- ~4,453 lines 코드
- 17/17 테스트 통과 (100%)
- Basel III, DORA, SR 21-14 준수

**Portfolio Spoke:**
- 8개 포트폴리오 관리 도구
- ~4,800 lines 코드
- 12/12 테스트 통과 (100%)
- Scipy 기반 구현

**전체:**
- ✅ 29개 MCP 도구
- ✅ 3개 MCP 서버 (100% 완료)
- ✅ 전문가급 금융 분석 플랫폼
- ✅ 프로젝트 완성도: ~85%

---

## 📂 Archive

오래된 문서 및 참고 자료는 [archive/](archive/) 폴더에 보관되어 있습니다.

**Archive 내용:**
- AI_INTEGRATION_GUIDE.md (구버전)
- FINANCIAL_PROJECTS_ANALYSIS.md (참고용)
- MARKET_SPOKE_TEST_REPORT.md (테스트 기록)
- MCP_SERVERS_GUIDE.md (구버전)
- RISK_SPOKE_USAGE.md (구버전)

---

## 🔗 관련 리소스

### 디렉토리
- **`/scripts/`** - 유틸리티 스크립트
- **`/services/`** - 마이크로서비스 코드
- **`/data/`** - 로컬 데이터셋

### 루트 문서
- **`../COMPLETED_FEATURES.md`** - 완료된 기능
- **`../PENDING_TASKS.md`** - 향후 계획
- **`../README.md`** - 프로젝트 메인

---

## 📝 문서 업데이트 이력

### 2025-10-04 - 문서 통일 및 정리 ✨
- ✅ 모든 spoke 문서 형식 통일
  - {SPOKE}_DESIGN.md - 설계 문서
  - {SPOKE}_USAGE.md - 사용 가이드
  - {SPOKE}_API_REFERENCE.md - API 레퍼런스 (Market만)
- ✅ Portfolio Spoke 문서 추가 (100% 완료)
- ✅ services 폴더의 MD 파일 docs로 이동
- ✅ 파일명 표준화 완료
- ✅ README 전면 재작성

### 이전 업데이트
- 2025-10-04: Risk Spoke 완전 구현 문서 추가
- 2025-10-04: Market Spoke 문서 완성
- 2025-10-04: 중복 문서 제거 및 archive 정리

---

**마지막 업데이트:** 2025-10-04
**문서 상태:** ✅ 최신 (완전히 통일됨)
**유지보수:** 지속적 업데이트 중

**총 핵심 문서:** 8개
- Market Spoke: 3개 (Design, Usage, API Reference)
- Risk Spoke: 2개 (Design, Usage)
- Portfolio Spoke: 3개 (Design, Usage, Research)
