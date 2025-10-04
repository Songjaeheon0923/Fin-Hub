# 📚 Archive - Reference Documentation

**참고 자료 및 테스트 가이드 모음**

---

## 📁 파일 구성

### 1. TESTING_GUIDE.md
**통합 테스트 가이드 - 3개 Spoke 전체 도구 (29개)**

**내용**:
- **Market Spoke**: 13개 도구 테스트 명령어
- **Risk Spoke**: 8개 도구 테스트 명령어
- **Portfolio Spoke**: 8개 도구 테스트 명령어
- Claude Desktop에서 직접 사용 가능한 예제
- 통합 테스트 시나리오 3가지

**사용 대상**:
- Claude Desktop 사용자
- QA 테스터
- 신규 개발자 온보딩

**예시**:
```
AAPL 주식의 최신 데이터를 가져와줘  # unified_market_data
AAPL의 VaR를 계산해줘              # var_calculator
AAPL, MSFT로 최적 포트폴리오를 만들어줘  # portfolio_optimizer
```

---

### 2. DATASET_REFERENCE.md
**데이터셋 완전 참조**

**내용**:
- **S&P 500 데이터셋**: 503개 종목, 5년 데이터, 71.4 MB
- **데이터 구조**: CSV 포맷, 컬럼 설명
- **데이터 품질**: 검증 결과 (99.98% 완전성)
- **다운로드 가이드**: 재다운로드 방법
- **캐싱 전략**: 메모리 및 디스크 캐시

**사용 대상**:
- 데이터 분석가
- 백엔드 개발자
- 시스템 관리자

**주요 정보**:
- 로컬 데이터 위치: `data/stock-data/`
- 메타데이터: `_metadata.json`
- 검증 리포트: `validation_report.json`

---

### 3. API_REFERENCE.md
**7개 외부 API 통합 명세**

**내용**:
- **Alpha Vantage**: 주식 시세, 기술 지표 (25 req/day)
- **CoinGecko**: 암호화폐 가격 (10-30 req/min)
- **News API**: 금융 뉴스 (100 req/day)
- **FRED**: 경제 지표 (Unlimited)
- **MarketStack**: 주식 백업 (1000 req/month)
- **Polygon.io**: 실시간 데이터 (선택사항)
- **Yahoo Finance**: 역사 데이터 (Unlimited)

**사용 대상**:
- API 통합 개발자
- DevOps 엔지니어
- 시스템 아키텍트

**주요 정보**:
- API 키 관리 (.env)
- Rate Limit 전략
- Fallback Chain
- 도구별 API 매핑

---

### 4. FINANCIAL_PROJECTS_ANALYSIS.md
**타 금융 프로젝트 분석**

**내용**:
- **TradeMaster (NTU)**: 강화학습 거래 플랫폼
- **Jesse AI**: 암호화폐 거래 봇
- **QuantConnect**: 알고리즘 거래 플랫폼
- **Backtrader**: 백테스팅 프레임워크
- **VectorBT**: 고성능 백테스팅

**분석 항목**:
- 데이터 활용 전략
- API 통합 방법
- 아키텍처 설계
- Fin-Hub 적용 가능한 아이디어

**사용 대상**:
- 제품 기획자
- 시니어 개발자
- 연구원

---

## 🎯 사용 시나리오

### 시나리오 1: 신규 개발자 온보딩
1. **DATASET_REFERENCE.md** - 데이터 구조 이해
2. **API_REFERENCE.md** - API 키 설정 및 테스트
3. **TESTING_GUIDE.md** - 각 도구 테스트 실행
4. **FINANCIAL_PROJECTS_ANALYSIS.md** - 업계 Best Practice 학습

---

### 시나리오 2: Claude Desktop 사용자
1. **TESTING_GUIDE.md** - 29개 도구 테스트 명령어 활용
2. 통합 시나리오로 실전 워크플로우 실습
3. 각 도구의 기능과 사용법 숙지

---

### 시나리오 3: 시스템 관리자
1. **API_REFERENCE.md** - Rate Limit 및 API 키 관리
2. **DATASET_REFERENCE.md** - 데이터 업데이트 및 검증
3. API Health Check 및 모니터링

---

## 📊 통계

**총 문서**: 4개
**총 도구 커버리지**: 29개 (Market 13 + Risk 8 + Portfolio 8)
**API 커버리지**: 7개 (6개 활성)
**데이터셋**: 503개 S&P 500 종목

---

## 🔗 관련 문서

### 설계 및 사용 가이드
- [Market Spoke Design](../market-spoke/MARKET_SPOKE_DESIGN.md)
- [Market Spoke Usage](../market-spoke/MARKET_SPOKE_USAGE.md)
- [Risk Spoke Design](../risk-spoke/RISK_SPOKE_DESIGN.md)
- [Risk Spoke Usage](../risk-spoke/RISK_SPOKE_USAGE.md)
- [Portfolio Spoke Design](../portfolio-spoke/PORTFOLIO_SPOKE_DESIGN.md)
- [Portfolio Spoke Usage](../portfolio-spoke/PORTFOLIO_SPOKE_USAGE.md)

### 프로젝트 문서
- [프로젝트 README](../../README.md)
- [완료된 기능](../../COMPLETED_FEATURES.md)
- [향후 계획](../../PENDING_TASKS.md)

---

## 📝 업데이트 이력

### 2025-10-04 - Archive 재구성 ✨
- ✅ TESTING_GUIDE.md 생성 (29개 도구 통합 테스트)
- ✅ DATASET_REFERENCE.md 생성 (데이터셋 완전 참조)
- ✅ API_REFERENCE.md 생성 (7개 API 명세)
- ✅ FINANCIAL_PROJECTS_ANALYSIS.md 유지 (타 프로젝트 분석)
- ✅ 불필요한 문서 5개 제거
  - AI_INTEGRATION_GUIDE.md (구버전)
  - api_specifications.json (API_REFERENCE.md로 대체)
  - MARKET_SPOKE_TEST_REPORT.md (TESTING_GUIDE.md로 통합)
  - MCP_SERVERS_GUIDE.md (docs/mcp/로 이동)
  - RISK_SPOKE_USAGE.md (docs/risk-spoke/로 이동)

---

**마지막 업데이트**: 2025-10-04
**상태**: ✅ 정리 완료
**파일 수**: 4개 (핵심 참조 문서만 유지)
