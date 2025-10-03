# Fin-Hub Documentation

**최고 수준의 금융 데이터 허브 - 전문 문서 센터**

---

## 📁 문서 구조

```
docs/
├── README.md                    ← 현재 파일 (문서 인덱스)
├── market-spoke/                ← Market Spoke (시장 데이터)
│   ├── MCP_TOOLS_USAGE_GUIDE.md
│   └── DATA_AND_API_REFERENCE.md
├── risk-spoke/                  ← Risk Spoke (리스크 관리)
│   ├── RISK_SPOKE_COMPLETE_USAGE.md
│   └── RISK_SPOKE_DESIGN.md
├── mcp/                         ← MCP 서버 통합
│   └── MCP_SERVERS_GUIDE.md
└── archive/                     ← 구버전/참고용
```

---

## 🚀 빠른 시작

### Market Spoke 사용하기
→ **[market-spoke/MCP_TOOLS_USAGE_GUIDE.md](market-spoke/MCP_TOOLS_USAGE_GUIDE.md)**
- 13개 시장 데이터 도구 사용법
- 주식, 암호화폐, 뉴스, 거시경제 데이터
- 실전 예제 및 API 매핑

### Risk Spoke 사용하기
→ **[risk-spoke/RISK_SPOKE_COMPLETE_USAGE.md](risk-spoke/RISK_SPOKE_COMPLETE_USAGE.md)**
- 8개 전문 리스크 관리 도구
- VaR, Stress Testing, Greeks, Compliance 등
- 종합 리스크 대시보드

### MCP 서버 설정
→ **[mcp/MCP_SERVERS_GUIDE.md](mcp/MCP_SERVERS_GUIDE.md)**
- MCP 서버 설치 및 설정
- Claude Desktop 통합
- 트러블슈팅

---

## 📊 Market Spoke (시장 데이터)

### [MCP_TOOLS_USAGE_GUIDE.md](market-spoke/MCP_TOOLS_USAGE_GUIDE.md)
**13개 MCP 도구 완전 가이드**

**도구 카테고리:**
1. **주식 데이터 (4개)**
   - `market.get_stock_price` - 실시간/역사적 주가
   - `market.get_company_info` - 기업 정보
   - `market.search_symbol` - 심볼 검색
   - `market.get_market_status` - 시장 상태

2. **암호화폐 (3개)**
   - `market.get_crypto_price` - 암호화폐 시세
   - `market.search_crypto` - 코인 검색
   - `market.get_crypto_market_data` - 시장 데이터

3. **분석 도구 (6개)**
   - Technical Analysis, Pattern Recognition
   - Anomaly Detection, Stock Comparison
   - Sentiment Analysis, Alert System

**100% 테스트 통과**

---

### [DATA_AND_API_REFERENCE.md](market-spoke/DATA_AND_API_REFERENCE.md)
**데이터셋 및 API 완전 참조**

**포함 내용:**
- 📦 로컬 데이터셋 (S&P 500, Gekko 암호화폐)
- 🔌 7개 외부 API (Finnhub, Alpha Vantage, MarketStack, CoinGecko, News API, FRED, OpenSanctions)
- 🗺️ MCP 도구 ↔ API 매핑
- 📥 다운로드 가이드
- 💡 사용 예제

**대상:** 개발자, 데이터 분석가

---

## 🎯 Risk Spoke (리스크 관리)

### [RISK_SPOKE_COMPLETE_USAGE.md](risk-spoke/RISK_SPOKE_COMPLETE_USAGE.md)
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
**규제 준수:** Basel III, DORA, SR 21-14

---

### [RISK_SPOKE_DESIGN.md](risk-spoke/RISK_SPOKE_DESIGN.md)
**Risk Spoke 아키텍처 및 설계 문서**

**포함 내용:**
- 시스템 아키텍처
- 도구별 상세 설계
- 방법론 및 알고리즘
- 데이터 플로우
- 통합 전략

**대상:** 아키텍트, 시니어 개발자

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

**대상:** DevOps, 시스템 관리자

---

## 📖 권장 읽기 순서

### 처음 시작하는 경우
1. **프로젝트 개요** → [../COMPLETED_FEATURES.md](../COMPLETED_FEATURES.md)
2. **Market Spoke** → [market-spoke/MCP_TOOLS_USAGE_GUIDE.md](market-spoke/MCP_TOOLS_USAGE_GUIDE.md)
3. **MCP 설정** → [mcp/MCP_SERVERS_GUIDE.md](mcp/MCP_SERVERS_GUIDE.md)

### 시장 데이터 분석
1. **도구 사용법** → [market-spoke/MCP_TOOLS_USAGE_GUIDE.md](market-spoke/MCP_TOOLS_USAGE_GUIDE.md)
2. **데이터 참조** → [market-spoke/DATA_AND_API_REFERENCE.md](market-spoke/DATA_AND_API_REFERENCE.md)

### 리스크 관리
1. **도구 가이드** → [risk-spoke/RISK_SPOKE_COMPLETE_USAGE.md](risk-spoke/RISK_SPOKE_COMPLETE_USAGE.md)
2. **설계 문서** → [risk-spoke/RISK_SPOKE_DESIGN.md](risk-spoke/RISK_SPOKE_DESIGN.md)

### 시스템 통합
1. **MCP 서버** → [mcp/MCP_SERVERS_GUIDE.md](mcp/MCP_SERVERS_GUIDE.md)
2. **API 참조** → [market-spoke/DATA_AND_API_REFERENCE.md](market-spoke/DATA_AND_API_REFERENCE.md)

---

## 🎯 빠른 참조

| 필요한 정보 | 문서 위치 |
|------------|----------|
| Market Spoke 도구 사용법 | [market-spoke/MCP_TOOLS_USAGE_GUIDE.md](market-spoke/MCP_TOOLS_USAGE_GUIDE.md) |
| Risk Spoke 도구 사용법 | [risk-spoke/RISK_SPOKE_COMPLETE_USAGE.md](risk-spoke/RISK_SPOKE_COMPLETE_USAGE.md) |
| 데이터셋 및 API 정보 | [market-spoke/DATA_AND_API_REFERENCE.md](market-spoke/DATA_AND_API_REFERENCE.md) |
| MCP 서버 설정 | [mcp/MCP_SERVERS_GUIDE.md](mcp/MCP_SERVERS_GUIDE.md) |
| Risk Spoke 설계 | [risk-spoke/RISK_SPOKE_DESIGN.md](risk-spoke/RISK_SPOKE_DESIGN.md) |
| 프로젝트 상태 | [../COMPLETED_FEATURES.md](../COMPLETED_FEATURES.md) |

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

**전체:**
- 21개 MCP 도구
- 2개 MCP 서버
- 전문가급 금융 분석 플랫폼

---

## 📂 Archive

오래된 문서 및 참고 자료는 [archive/](archive/) 폴더에 보관되어 있습니다.

**Archive 내용:**
- AI_INTEGRATION_GUIDE.md (구버전)
- FINANCIAL_PROJECTS_ANALYSIS.md (참고용)
- RISK_SPOKE_USAGE.md (구버전, COMPLETE_USAGE로 대체)
- api_specifications.json (레거시)
- MARKET_SPOKE_TEST_REPORT.md (테스트 기록)

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

### 2025-10-04 - 대대적 정리 ✨
- ✅ 폴더 구조 재편성 (market-spoke, risk-spoke, mcp, archive)
- ✅ Risk Spoke 완전 구현 문서 추가 (8개 도구)
- ✅ 중복/구식 문서 archive로 이동
- ✅ README 전면 재작성 (체계적 인덱스)
- ✅ 문서 수: 11개 → 5개 핵심 문서 + archive

### 이전 업데이트
- 2025-10-04: Market Spoke 문서 완성
- 2025-10-04: 중복 문서 제거 (36% 감소)
- 2025-10-04: DATA_AND_API_REFERENCE 통합 생성

---

**마지막 업데이트:** 2025-10-04
**문서 상태:** ✅ 최신 (깔끔하게 정리됨)
**유지보수:** 지속적 업데이트 중
