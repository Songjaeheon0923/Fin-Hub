# Fin-Hub: AI 금융 도구 통합 허브

## 프로젝트 개요
Fin-Hub는 AI 에이전트가 활용할 수 있는 금융 분석 도구들을 통합하는 중앙 허브 플랫폼입니다. Hub-and-Spoke 아키텍처를 통해 분산된 금융 AI 도구들을 MCP(Model Context Protocol) 표준으로 통합하여 제공합니다.

## 아키텍처 개요
```
fin-hub/
├── infrastructure/          # 인프라 설정 (Consul, NGINX, Monitoring)
├── services/               # 핵심 서비스들
│   ├── hub-server/         # 중앙 허브 서비스
│   ├── market-spoke/       # 시장 분석 도구
│   ├── risk-spoke/         # 리스크 관리 도구
│   └── pfolio-spoke/       # 포트폴리오 관리 도구
├── shared/                 # 공통 라이브러리 및 스키마
├── documentation/          # 프로젝트 문서
├── deployment/            # 배포 설정 (Docker, K8s, Terraform)
├── tests/                 # 테스트 코드
├── scripts/               # 유틸리티 스크립트
├── tools/                 # 개발 도구 및 SDK
├── examples/              # 사용 예제
└── assets/                # 이미지, 다이어그램 등
```

## 빠른 시작

### 1. 전체 시스템 실행
```bash
# 환경 설정 및 전체 시스템 시작
./scripts/setup/init.sh
docker-compose up -d
```

### 2. 개별 서비스 테스트
```bash
# Market Analysis 도구 테스트
curl http://localhost:8001/tools/market/get_price

# Risk Management 도구 테스트
curl http://localhost:8002/tools/risk/detect_anomaly

# Portfolio Management 도구 테스트
curl http://localhost:8003/tools/pfolio/generate_optimal
```

## 서비스 구성

### Hub Server (Port: 8000)
- **Service Registry**: 도구 등록 및 발견
- **API Gateway**: 요청 라우팅 및 로드 밸런싱
- **Tool Execution**: 통합 실행 엔진

### Market Spoke (Port: 8001)
- **가격 분석**: 실시간 주가 데이터 조회
- **변동성 예측**: AI 기반 시장 변동성 분석
- **감성 분석**: 뉴스/소셜미디어 감성 분석

### Risk Spoke (Port: 8002)
- **이상 거래 탐지**: ML 기반 이상 거래 패턴 감지
- **컴플라이언스 체크**: 규제 준수 여부 확인

### Portfolio Spoke (Port: 8003)
- **최적화**: 리스크 대비 수익률 최적화
- **리밸런싱**: 포트폴리오 재조정 알고리즘
- **소비 분석**: 개인 재무 패턴 분석

## 개발 환경 설정

### 필수 요구사항
- Docker & Docker Compose
- Python 3.11+
- Node.js (문서 생성용)

### 로컬 개발 환경
```bash
# 개발 환경 초기화
make setup-dev

# 서비스별 개발 서버 시작
make dev-hub        # Hub Server
make dev-market     # Market Spoke
make dev-risk       # Risk Spoke
make dev-pfolio     # Portfolio Spoke
```

## 문서

- [설치 가이드](documentation/setup/INSTALLATION.md)
- [API 문서](documentation/api/README.md)
- [아키텍처 가이드](documentation/architecture/README.md)
- [MCP 클라이언트 연동](documentation/guides/MCP_INTEGRATION.md)
- [배포 가이드](documentation/deployment/README.md)

## 라이선스
MIT License

## 기여 방법
기여 방법은 [CONTRIBUTING.md](CONTRIBUTING.md)를 참고해 주세요.