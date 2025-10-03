# Fin-Hub 문서 디렉토리

## 📚 문서 개요

이 디렉토리는 Fin-Hub 프로젝트의 모든 주요 문서를 포함합니다.

---

## 🗂️ 문서 구조

### 1. 핵심 참조 문서

#### 📊 [DATA_AND_API_REFERENCE.md](DATA_AND_API_REFERENCE.md) ⭐ **가장 중요**
- **용도**: 모든 데이터셋과 API에 대한 완전한 참조
- **포함 내용**:
  - 로컬 데이터셋 (S&P 500, 암호화폐, Gekko)
  - 7개 API 상세 정보 (Finnhub, Alpha Vantage, MarketStack, CoinGecko, News API, FRED, OpenSanctions)
  - MCP 도구 매핑 (어떤 도구가 어떤 API/데이터를 사용하는지)
  - 다운로드 가이드 및 사용 예제
- **대상**: 개발자, 데이터 분석가, API 사용자

#### 📋 프로젝트 상태 (루트 디렉토리)
- **[../COMPLETED_FEATURES.md](../COMPLETED_FEATURES.md)** - 완료된 기능 목록
- **[../PENDING_TASKS.md](../PENDING_TASKS.md)** - 대기 중인 작업 및 16주 로드맵
- **대상**: 프로젝트 관리자, 개발 팀

#### ✅ [MARKET_SPOKE_TEST_REPORT.md](MARKET_SPOKE_TEST_REPORT.md)
- **용도**: Market Spoke 서비스 테스트 결과
- **포함 내용**:
  - 6/6 MCP 도구 테스트 결과
  - API 성능 벤치마크
  - 사용 가능한 기능 목록
  - 다음 단계 권장 사항
- **대상**: QA, 개발자, 운영 팀

---

### 2. 전문 가이드

#### 🤖 [AI_INTEGRATION_GUIDE.md](AI_INTEGRATION_GUIDE.md)
- **용도**: AI 에이전트가 Fin-Hub API를 사용하는 방법
- **포함 내용**:
  - 의도 분류 로직
  - API 선택 결정 트리
  - 응답 포맷팅 가이드
  - 실전 예제
- **대상**: AI 개발자, LLM 통합 개발자

#### 🚀 [GEKKO_QUICK_START.md](GEKKO_QUICK_START.md)
- **용도**: Gekko 암호화폐 데이터 다운로드 빠른 시작
- **포함 내용**:
  - 수동 다운로드 방법 (권장)
  - 자동 다운로드 스크립트
  - 데이터 검증
  - 사용 예제
- **대상**: 암호화폐 데이터 분석가, 백테스팅 개발자

#### 📈 [FINANCIAL_PROJECTS_ANALYSIS.md](FINANCIAL_PROJECTS_ANALYSIS.md)
- **용도**: 성공적인 오픈소스 금융 프로젝트 분석
- **포함 내용**:
  - TradeMaster, Jesse AI, FinRL 등 분석
  - 데이터 전략 비교
  - Fin-Hub에 적용 가능한 아이디어
- **대상**: 아키텍트, 전략 기획자

---

### 3. 기술 참조

#### 🔧 [api_specifications.json](api_specifications.json)
- **용도**: API 엔드포인트 및 스키마 정의 (JSON 형식)
- **포함 내용**:
  - 모든 MCP 도구의 JSON 스키마
  - 입력/출력 형식
  - 예제 요청/응답
- **대상**: API 클라이언트 개발자, 자동화 도구

---

## 📖 문서 읽기 순서 (추천)

### 처음 시작하는 경우
1. **[../COMPLETED_FEATURES.md](../COMPLETED_FEATURES.md)** - 프로젝트 전체 이해
2. **[DATA_AND_API_REFERENCE.md](DATA_AND_API_REFERENCE.md)** - 사용 가능한 데이터/API 파악
3. **[MARKET_SPOKE_TEST_REPORT.md](MARKET_SPOKE_TEST_REPORT.md)** - 테스트 결과 및 성능 확인

### API 사용 개발
1. **[DATA_AND_API_REFERENCE.md](DATA_AND_API_REFERENCE.md)** - API 및 도구 참조
2. **[api_specifications.json](api_specifications.json)** - JSON 스키마 확인
3. **[AI_INTEGRATION_GUIDE.md](AI_INTEGRATION_GUIDE.md)** - AI 통합 (선택)

### 데이터 분석/백테스팅
1. **[DATA_AND_API_REFERENCE.md](DATA_AND_API_REFERENCE.md)** - 데이터셋 파악
2. **[GEKKO_QUICK_START.md](GEKKO_QUICK_START.md)** - Gekko 데이터 다운로드 (선택)
3. **[FINANCIAL_PROJECTS_ANALYSIS.md](FINANCIAL_PROJECTS_ANALYSIS.md)** - 전략 아이디어

---

## 🎯 빠른 참조

### 데이터셋 정보가 필요하면
→ **[DATA_AND_API_REFERENCE.md](DATA_AND_API_REFERENCE.md)** 섹션 1-3

### API 사용법이 궁금하면
→ **[DATA_AND_API_REFERENCE.md](DATA_AND_API_REFERENCE.md)** 섹션 4-5

### 프로젝트 진행 상황이 궁금하면
→ **[../COMPLETED_FEATURES.md](../COMPLETED_FEATURES.md)** 및 **[../PENDING_TASKS.md](../PENDING_TASKS.md)**

### 테스트 결과가 필요하면
→ **[MARKET_SPOKE_TEST_REPORT.md](MARKET_SPOKE_TEST_REPORT.md)**

### Gekko 데이터 다운로드가 필요하면
→ **[GEKKO_QUICK_START.md](GEKKO_QUICK_START.md)**

### AI 통합이 필요하면
→ **[AI_INTEGRATION_GUIDE.md](AI_INTEGRATION_GUIDE.md)**

---

## 📝 문서 업데이트 이력

### 2025-10-04
- ✅ 중복 문서 5개 제거:
  - `GEKKO_DATA_DOWNLOAD_GUIDE.md` (GEKKO_QUICK_START.md로 통합)
  - `GEKKO_DOWNLOAD_INSTRUCTIONS.md` (GEKKO_QUICK_START.md로 통합)
  - `API_INTEGRATION_COMPLETE.md` (MARKET_SPOKE_TEST_REPORT.md로 통합)
  - `PROJECT_CLEANUP_REPORT.md` (정보 통합 후 제거)
  - `COMPLETE_FEATURES_SUMMARY.md` (루트의 COMPLETED_FEATURES.md 사용)
- ✅ `DATA_AND_API_REFERENCE.md` 생성 (모든 데이터/API 정보 통합)
- ✅ 프로젝트 상태 관리를 루트 디렉토리로 일원화
- ✅ 문서 수 감소: 11개 → 7개 (36% 감소)

---

## 🔗 관련 디렉토리

- **`/scripts/`** - 유틸리티 스크립트 (데이터 다운로드, 검증, 테스트)
- **`/services/`** - 마이크로서비스 코드
- **`/data/`** - 로컬 데이터셋 저장소

---

## 💡 기여 가이드

문서 작성 시:
1. **간결성**: 핵심 정보만 포함
2. **예제**: 실제 사용 가능한 코드 예제 제공
3. **구조화**: 명확한 섹션 구분
4. **최신 유지**: 코드 변경 시 문서도 업데이트

---

**마지막 업데이트**: 2025-10-04
**문서 개수**: 7개 (1 README + 6 문서)
**프로젝트 상태**: 루트의 COMPLETED_FEATURES.md 및 PENDING_TASKS.md 참조
**유지보수 상태**: ✅ 정리 완료
