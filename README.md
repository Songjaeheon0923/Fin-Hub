# Fin-Hub: AI 금융 도구 통합 허브

## 프로젝트 개요
Fin-Hub는 AI 에이전트가 활용할 수 있는 금융 분석 도구들을 통합하는 중앙 허브 플랫폼입니다. Hub-and-Spoke 아키텍처를 통해 분산된 금융 AI 도구들을 MCP(Model Context Protocol) 표준으로 통합하여 제공합니다.

## 주요 기능

### 🎯 MCP (Model Context Protocol) 지원
- Claude Desktop 및 다른 AI 클라이언트와 직접 연동
- 4개의 독립적인 MCP 서버 (Hub, Market, Risk, Portfolio)
- 실시간 시장 데이터, 리스크 분석, 포트폴리오 최적화 도구 제공

### 📊 시장 데이터 분석 (Market Spoke)
- 실시간 주식 시세 조회
- 암호화폐 가격 추적
- 금융 뉴스 검색
- 경제 지표 데이터 (GDP, CPI 등)
- 다중 API fallback 지원

### 🛡️ 리스크 관리 (Risk Spoke)
- 이상 거래 패턴 탐지
- 포트폴리오 컴플라이언스 체크
- 통계 기반 이상치 분석

### 💼 포트폴리오 관리 (Portfolio Spoke)
- 리스크-수익률 기반 포트폴리오 최적화
- 자동 리밸런싱 계산
- 포트폴리오 성과 분석 및 손익 계산

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

### 1. MCP 서버 설정 (Claude Desktop 연동)

#### 환경 변수 설정
프로젝트 루트에 `.env` 파일을 생성하고 필요한 API 키를 설정하세요:

```bash
# Market Data APIs
ALPHA_VANTAGE_API_KEY=your_key_here
NEWS_API_KEY=your_key_here
COINGECKO_API_KEY=your_key_here
FRED_API_KEY=your_key_here
FINNHUB_API_KEY=your_key_here
MARKETSTACK_API_KEY=your_key_here
OPENSANCTIONS_API_KEY=your_key_here
```

**주의:** `.env` 파일은 gitignore에 포함되어 있으므로 git에 커밋되지 않습니다.

#### Claude Desktop 설정

1. Claude Desktop 설정 파일 열기:
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

2. 다음 설정을 `mcpServers` 섹션에 추가:

```json
{
  "mcpServers": {
    "fin-hub": {
      "command": "python",
      "args": ["C:/project/Fin-Hub/services/hub-server/app/mcp_server.py"],
      "env": {
        "ENVIRONMENT": "development"
      }
    },
    "fin-hub-market": {
      "command": "python",
      "args": ["C:/project/Fin-Hub/services/market-spoke/mcp_server.py"],
      "env": {
        "ENVIRONMENT": "development",
        "ALPHA_VANTAGE_API_KEY": "your_key",
        "NEWS_API_KEY": "your_key",
        "COINGECKO_API_KEY": "your_key",
        "FRED_API_KEY": "your_key",
        "FINNHUB_API_KEY": "your_key"
      }
    },
    "fin-hub-risk": {
      "command": "python",
      "args": ["C:/project/Fin-Hub/services/risk-spoke/mcp_server.py"],
      "env": {
        "ENVIRONMENT": "development"
      }
    },
    "fin-hub-portfolio": {
      "command": "python",
      "args": ["C:/project/Fin-Hub/services/pfolio-spoke/mcp_server.py"],
      "env": {
        "ENVIRONMENT": "development"
      }
    }
  }
}
```

**주의:** 경로를 실제 프로젝트 경로로 변경하세요.

3. Claude Desktop 재시작

4. Claude Desktop에서 `/mcp` 명령어로 서버 확인

### 2. MCP 서버 사용 예시

```
# 주식 시세 조회
AAPL 주식의 현재 시세를 알려줘

# 암호화폐 가격 조회
비트코인 가격을 알려줘

# 금융 뉴스 검색
테슬라 관련 최신 뉴스를 찾아줘

# 포트폴리오 최적화
다음 자산들로 moderate 리스크의 포트폴리오를 최적화해줘:
[
  {"symbol": "AAPL", "expected_return": 0.12, "risk": 0.15},
  {"symbol": "GOOGL", "expected_return": 0.15, "risk": 0.20}
]

# 이상치 탐지
데이터 [10, 12, 11, 13, 100, 12, 11]에서 이상치를 찾아줘
```

자세한 사용법은 [MCP 서버 가이드](docs/MCP_SERVERS_GUIDE.md)를 참고하세요.

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

### MCP 서버 관련
- **[MCP 서버 사용 가이드](docs/MCP_SERVERS_GUIDE.md)** - 각 MCP 서버의 도구 사용법 및 예시
- **[데이터 및 API 레퍼런스](docs/DATA_AND_API_REFERENCE.md)** - API 데이터 소스 및 검증 정보
- **[Market Spoke 테스트 리포트](docs/MARKET_SPOKE_TEST_REPORT.md)** - Market Spoke 통합 테스트 결과

### 프로젝트 관리
- [설치 가이드](documentation/setup/INSTALLATION.md)
- [API 문서](documentation/api/README.md)
- [아키텍처 가이드](documentation/architecture/README.md)
- [배포 가이드](documentation/deployment/README.md)

## 보안 및 주의사항

### API 키 관리
- **절대로 API 키를 git에 커밋하지 마세요**
- `.env` 파일과 `claude_desktop_config.json`은 `.gitignore`에 포함되어 있습니다
- API 키는 환경 변수로만 관리하세요
- 공개 저장소에 업로드하기 전에 모든 민감한 정보를 제거했는지 확인하세요

### gitignore 포함 항목
- `.env*` - 모든 환경 변수 파일
- `claude_desktop_config.json` - Claude Desktop 설정 (API 키 포함)
- `*_API_KEY*`, `*_SECRET*`, `*credentials*` - API 키 및 비밀 정보
- `*.pem`, `*.key` - 인증서 및 키 파일

## 데이터 소스

### Market Data Providers
- **Alpha Vantage** - 주식 시세 데이터
- **CoinGecko** - 암호화폐 가격 데이터
- **News API** - 금융 뉴스
- **FRED (Federal Reserve Economic Data)** - 경제 지표
- **Finnhub** - 실시간 주식 데이터
- **Marketstack** - 주식 시장 데이터
- **OpenSanctions** - 제재 대상 확인

각 API의 무료 티어 제한을 확인하고 사용하세요.

## 라이선스
MIT License

## 기여 방법
기여 방법은 [CONTRIBUTING.md](CONTRIBUTING.md)를 참고해 주세요.

## 연락처
문제가 있거나 질문이 있으시면 Issue를 생성해 주세요.