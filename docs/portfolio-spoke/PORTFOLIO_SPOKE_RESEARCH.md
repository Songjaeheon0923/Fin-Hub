# Portfolio Spoke 리서치 및 설계 방향

**연구 수행일**: 2025-10-04
**목적**: Portfolio Spoke 구현을 위한 업계 베스트 프랙티스 분석 및 설계 방향 수립

---

## 📊 Executive Summary

### 주요 발견사항
1. **2025년 트렌드**: 전통적 주식-채권 상관관계 붕괴, 대체 자산 포함, 세금 최적화 중요성 증가
2. **핵심 기술**: PyPortfolioOpt, skfolio (2025 신규), Riskfolio-Lib이 주요 Python 라이브러리
3. **전문가 전략**: Factor Investing, Smart Beta, HRP (Hierarchical Risk Parity), Black-Litterman
4. **필요 데이터**: 실시간 가격, 역사적 수익률, 팩터 데이터, 거시경제 지표

---

## 🔍 1. 현재 개발 트렌드 분석

### 1.1 주요 오픈소스 프로젝트

#### Ghostfolio (Angular + NestJS + Prisma)
- **특징**: 프라이버시 중심 자산 관리 소프트웨어
- **기능**: 주식, ETF, 암호화폐 추적
- **Stack**: TypeScript, 100% 오픈소스
- **시사점**: 사용자 데이터 프라이버시가 핵심 가치

#### Portfolio Performance
- **특징**: 오프라인 포트폴리오 추적
- **기능**: 성과 분석, 벤치마크 비교
- **시사점**: 로컬 데이터 저장, 보안 중시

### 1.2 Python 라이브러리 생태계

#### PyPortfolioOpt (가장 널리 사용됨)
```python
주요 기능:
- Mean-Variance Optimization
- Efficient Frontier 계산
- Black-Litterman 자산 배분
- Hierarchical Risk Parity (HRP)
- Shrinkage 기법 (노이즈 감소)
- 모듈식 설계 (사용자 정의 가능)
```

#### skfolio (2025년 7월 출시, 최신)
```python
특징:
- scikit-learn 생태계와 완벽 통합
- 포트폴리오 구성 및 리스크 관리
- 학계에서 인정받은 새로운 라이브러리
- 최신 연구 결과 반영
```

#### Riskfolio-Lib
```python
강점:
- 다양한 리스크 모델
- CVaR, MAD, CDaR 등 다양한 리스크 측정
- 전문가급 최적화 알고리즘
```

### 1.3 백테스팅 프레임워크

#### VectorBT (최고 성능)
- NumPy 기반 벡터화 연산
- Numba 컴파일로 최고 속도
- 대규모 시뮬레이션에 적합

#### Zipline-Reloaded (2025년 업데이트)
- Quantopian 레거시
- 10년 분량 미국 주식 분봉 데이터
- Factor-based 리서치에 적합
- StrateQueue로 실제 거래 연결 가능

#### Backtrader (가장 널리 사용)
- 풍부한 문서화
- CSV, DataFrame, 실시간 데이터 지원
- 3개 브로커와 연동

---

## 💼 2. 전문 투자자 포트폴리오 전략

### 2.1 2025년 핵심 트렌드

#### 트렌드 1: 전통적 주식-채권 상관관계 붕괴
```
문제점:
- 주식-채권 간 전통적 음의 상관관계 약화
- 분산 투자 효과 감소
- 인플레이션, 정책, 재정 불균형이 원인

해결책:
- Liquid Alternatives (유동성 있는 대체자산)
- Digital Assets (디지털 자산)
- International Equities (국제 주식)
```

#### 트렌드 2: 세금 최적화의 중요성 증가
```
주요 기법:
- Tax Loss Harvesting (세금 손실 수확)
- 포트폴리오 커스터마이제이션
- 75% 기관투자자가 최우선 기능으로 선택
```

#### 트렌드 3: 암호화폐 편입 증가
```
통계:
- 75% 기관투자자가 2025년 암호화폐 비중 증가 계획
- 59%가 AUM의 5% 이상 목표
- 분산 투자 도구로 인식
```

### 2.2 주요 자산 배분 전략

#### Strategic Asset Allocation (전략적 자산 배분)
```yaml
특징:
  - 장기 목표 기반
  - 정기적 리뷰 및 조정
  - 동적 프레임워크 (고정 앵커 아님)

핵심 목표:
  - 리스크 조정 수익률 극대화 (44% 어드바이저)
  - 분산 및 자산 클래스 커버리지 (41%)
```

#### Factor Investing (팩터 투자)
```yaml
주요 팩터:
  - Momentum (모멘텀)
  - Value (가치)
  - Quality (품질)
  - Low Volatility (저변동성)
  - Size (시가총액)

구현:
  - Smart Beta ETF
  - Factor Portfolio 직접 구성
  - Multi-Factor 전략
```

#### Hierarchical Risk Parity (HRP)
```yaml
장점:
  - Mean-Variance의 불안정성 극복
  - 계층적 클러스터링 사용
  - 추정 오류에 강인함
  - 다양한 자산군에 적용 가능
```

---

## 🔧 3. 필요한 API 및 기능

### 3.1 핵심 Portfolio Management API

#### 1. Portfolio Optimization API
```python
기능:
  - Mean-Variance Optimization
  - Black-Litterman 모델
  - Hierarchical Risk Parity
  - Risk Parity
  - Minimum Volatility
  - Maximum Sharpe Ratio
  - Maximum Sortino Ratio

입력:
  - 자산 리스트 (symbols)
  - 기대 수익률 (optional, 계산 가능)
  - 리스크 모델 선택
  - 제약 조건 (최소/최대 비중, 섹터 제한 등)

출력:
  - 최적 가중치
  - 예상 수익률
  - 예상 변동성
  - Sharpe Ratio
  - Efficient Frontier 데이터
```

#### 2. Portfolio Rebalancing API
```python
기능:
  - 목표 배분 대비 현재 배분 분석
  - 매수/매도 액션 제안
  - 거래 비용 최적화
  - 세금 효율적 리밸런싱
  - 리밸런싱 스케줄링 (주기, 임계값 기반)

입력:
  - 현재 포지션
  - 목표 가중치
  - 거래 비용
  - 세금 고려사항
  - 리밸런싱 전략 (임계값, 주기)

출력:
  - 매수/매도 수량
  - 예상 거래 비용
  - 세금 영향
  - 리밸런싱 후 포트폴리오
```

#### 3. Portfolio Performance API
```python
기능:
  - 수익률 계산 (일별, 주별, 월별, 연간)
  - 벤치마크 대비 성과
  - Attribution Analysis (성과 귀속 분석)
  - Drawdown 분석
  - Rolling 통계

입력:
  - 포트폴리오 구성
  - 기간
  - 벤치마크 (선택)

출력:
  - Total Return
  - Annualized Return
  - Volatility
  - Sharpe Ratio, Sortino Ratio
  - Max Drawdown
  - Alpha, Beta (벤치마크 대비)
  - Attribution by asset/sector
```

#### 4. Portfolio Backtesting API
```python
기능:
  - 역사적 데이터로 전략 시뮬레이션
  - Walk-Forward Analysis
  - Monte Carlo 시뮬레이션
  - 거래 비용 포함

입력:
  - 전략 정의 (리밸런싱 규칙 등)
  - 백테스트 기간
  - 초기 자본
  - 거래 비용 모델

출력:
  - 성과 지표
  - 거래 내역
  - Equity Curve
  - 연도별 수익률
```

#### 5. Factor Analysis API
```python
기능:
  - Factor Exposure 분석
  - Factor Return 계산
  - Factor Attribution
  - Style Analysis

입력:
  - 포트폴리오 또는 자산
  - 팩터 모델 선택 (Fama-French, Custom 등)

출력:
  - Factor Loadings
  - Factor Returns
  - 설명된 수익률
  - Residual Risk
```

#### 6. Asset Allocation API
```python
기능:
  - Strategic Asset Allocation
  - Tactical Asset Allocation
  - 다각화 분석
  - 상관관계 분석

입력:
  - 자산 유니버스
  - 투자 목표 (수익률 목표, 리스크 허용도)
  - 투자 제약

출력:
  - 추천 자산 배분
  - 예상 성과
  - 리스크 분석
  - 시나리오 분석
```

#### 7. Tax Optimization API
```python
기능:
  - Tax Loss Harvesting 기회 식별
  - 세금 효율적 포트폴리오 구성
  - Wash Sale 규칙 준수
  - Capital Gains 최적화

입력:
  - 포트폴리오 포지션
  - 취득 가격 및 날짜
  - 세율 정보

출력:
  - Tax Loss Harvesting 기회
  - 대체 자산 제안
  - 예상 세금 절감
  - 세후 수익률
```

### 3.2 추가 데이터 API (외부 통합)

#### 이미 보유한 API ✅
```yaml
Alpha Vantage:
  - 주식 가격 ✅
  - 기술적 지표 ✅

CoinGecko:
  - 암호화폐 가격 ✅

FRED:
  - 거시경제 지표 ✅
  - 무위험 수익률 (Treasury) ✅
```

#### 필요한 추가 API 🔄

##### 1. ETF 데이터
```yaml
필요성: ETF는 포트폴리오 구성의 핵심
데이터:
  - ETF Holdings (구성 종목)
  - Expense Ratio (비용)
  - AUM (자산 규모)
  - Distribution (배당)
  - Tracking Error (추적 오차)

API 옵션:
  - ETF Database API
  - Alpha Vantage (일부 지원)
  - Finnhub (ETF profile)
```

##### 2. 팩터 데이터
```yaml
필요성: Factor Investing 구현
데이터:
  - Fama-French Factors (HML, SMB, MOM 등)
  - Custom Factors (Quality, Low Vol 등)
  - Factor Returns

API 옵션:
  - Kenneth French Data Library (무료)
  - AQR Capital (무료 팩터 데이터)
  - 자체 계산 (S&P 500 데이터 활용)
```

##### 3. 벤치마크 인덱스
```yaml
필요성: 성과 비교
데이터:
  - S&P 500, NASDAQ, Russell 2000
  - 글로벌 인덱스 (MSCI World 등)
  - 채권 인덱스

API 옵션:
  - Yahoo Finance (무료)
  - Alpha Vantage (일부)
  - 자체 계산 (S&P 500 보유)
```

##### 4. 기업 펀더멘털
```yaml
필요성: Fundamental-based 자산 배분
데이터:
  - P/E, P/B, ROE, ROA
  - Revenue, Earnings
  - Debt Ratios

API 옵션:
  - Alpha Vantage (Fundamental Data) ✅
  - Financial Modeling Prep
  - Finnhub
```

---

## 📚 4. 권장 구현 방향

### 4.1 우선순위 1: 핵심 포트폴리오 기능 (Week 1-2)

#### 구현할 API
1. **Portfolio Optimization**
   - PyPortfolioOpt 라이브러리 활용
   - Mean-Variance, HRP, Black-Litterman
   - Efficient Frontier 시각화 지원

2. **Portfolio Rebalancing**
   - 목표 대비 현재 배분 분석
   - 거래 비용 고려한 리밸런싱
   - 리밸런싱 액션 제안

3. **Portfolio Performance**
   - 수익률, 변동성, Sharpe/Sortino
   - 벤치마크 대비 분석
   - Drawdown 분석

### 4.2 우선순위 2: 고급 분석 기능 (Week 3-4)

#### 구현할 API
4. **Portfolio Backtesting**
   - VectorBT 또는 간단한 자체 구현
   - 전략 시뮬레이션
   - 성과 지표 계산

5. **Factor Analysis**
   - Fama-French 3-Factor 모델
   - Factor Exposure 분석
   - Factor Attribution

6. **Asset Allocation**
   - Strategic vs Tactical
   - 상관관계 기반 분산 투자
   - 시나리오 분석

### 4.3 우선순위 3: 최적화 기능 (Week 5-6)

#### 구현할 API
7. **Tax Optimization**
   - Tax Loss Harvesting
   - 세후 수익률 최적화
   - Wash Sale 규칙

8. **Smart Beta / Factor Portfolios**
   - Momentum, Value, Quality 팩터
   - Smart Beta 포트폴리오 구성
   - Multi-Factor 전략

### 4.4 필요한 Python 라이브러리

```python
# 핵심 라이브러리
pip install pyportfolioopt      # 포트폴리오 최적화
pip install riskfolio-lib        # 고급 리스크 관리
pip install skfolio              # 최신 포트폴리오 구성 (2025)

# 백테스팅
pip install vectorbt             # 고성능 백테스팅
pip install backtrader           # 종합 백테스팅 프레임워크

# 분석 도구
pip install alphalens            # 팩터 분석
pip install pyfolio              # 성과 분석
pip install empyrical            # 성과 지표 계산

# 이미 보유
pip install pandas numpy scipy   # 데이터 처리
pip install matplotlib seaborn   # 시각화
```

### 4.5 데이터 요구사항

#### 로컬 데이터 활용 ✅
```yaml
S&P 500 주식 데이터 (보유):
  - 5년 일별 OHLCV
  - 503개 종목
  - 포트폴리오 백테스팅 가능
  - 상관관계 분석 가능
```

#### 추가 필요 데이터
```yaml
ETF 데이터:
  - 주요 ETF 목록 (SPY, QQQ, IWM 등)
  - ETF Holdings
  - Expense Ratios

팩터 데이터:
  - Fama-French 3-Factor 데이터
  - Kenneth French 웹사이트에서 무료 다운로드
  - 또는 S&P 500 데이터로 자체 계산

벤치마크:
  - S&P 500 인덱스 데이터 (보유 종목으로 계산 가능)
  - 무위험 수익률 (FRED에서 Treasury 수익률 가져오기 ✅)
```

---

## 🎯 5. 권장 Portfolio Spoke 아키텍처

### 5.1 도구 구성 (8개 도구)

```
Portfolio Spoke
├── 1. portfolio_optimizer       (포트폴리오 최적화)
│   ├── Mean-Variance
│   ├── Black-Litterman
│   ├── HRP
│   └── Risk Parity
│
├── 2. portfolio_rebalancer      (리밸런싱)
│   ├── 비중 차이 분석
│   ├── 거래 액션 생성
│   └── 거래 비용 최적화
│
├── 3. portfolio_analyzer        (성과 분석)
│   ├── 수익률/변동성 계산
│   ├── Sharpe/Sortino Ratio
│   ├── Drawdown 분석
│   └── 벤치마크 비교
│
├── 4. backtester               (백테스팅)
│   ├── 전략 시뮬레이션
│   ├── Walk-Forward Analysis
│   └── 성과 지표 계산
│
├── 5. factor_analyzer          (팩터 분석)
│   ├── Factor Exposure
│   ├── Factor Returns
│   └── Attribution Analysis
│
├── 6. asset_allocator          (자산 배분)
│   ├── Strategic Allocation
│   ├── Tactical Allocation
│   └── 상관관계 분석
│
├── 7. tax_optimizer            (세금 최적화)
│   ├── Tax Loss Harvesting
│   └── 세후 수익률 계산
│
└── 8. portfolio_dashboard      (종합 대시보드)
    ├── 전체 포트폴리오 요약
    ├── 리스크 지표
    ├── 성과 지표
    └── 권장사항
```

### 5.2 데이터 플로우

```
Input Sources
├── Market Spoke (13 tools)
│   ├── 주식 가격 데이터
│   ├── 기술적 지표
│   └── 시장 데이터
│
├── Risk Spoke (8 tools)
│   ├── VaR, CVaR
│   ├── 리스크 지표
│   └── 리스크 대시보드
│
├── Local Data
│   ├── S&P 500 역사 데이터
│   └── 포트폴리오 포지션
│
└── External APIs
    ├── FRED (무위험 수익률)
    ├── Fama-French (팩터 데이터)
    └── ETF 데이터 (필요 시)

↓↓↓

Portfolio Spoke (8 tools)
- 최적화, 리밸런싱, 분석, 백테스팅

↓↓↓

Output
├── 최적 포트폴리오 가중치
├── 리밸런싱 액션
├── 성과 리포트
└── 투자 권장사항
```

### 5.3 통합 전략

#### Market Spoke 연동
```python
# Portfolio Spoke에서 Market Spoke 도구 활용
from market_spoke import UnifiedMarketDataTool, TechnicalAnalysisTool

# 가격 데이터 가져오기
market_data = UnifiedMarketDataTool()
prices = market_data.get_historical_prices(symbols, period)

# 기술적 지표 활용
technical = TechnicalAnalysisTool()
momentum = technical.calculate_rsi(symbol)  # Momentum factor
```

#### Risk Spoke 연동
```python
# Risk Spoke 도구 활용
from risk_spoke import VaRCalculatorTool, RiskMetricsTool

# 포트폴리오 VaR 계산
var_tool = VaRCalculatorTool()
portfolio_var = var_tool.calculate_portfolio_var(weights, symbols)

# Sharpe Ratio 등 리스크 지표
metrics = RiskMetricsTool()
sharpe = metrics.calculate_sharpe_ratio(portfolio_returns)
```

---

## 📊 6. 경쟁 분석

### Ghostfolio vs Fin-Hub Portfolio Spoke

| 기능 | Ghostfolio | Fin-Hub Portfolio Spoke |
|------|-----------|------------------------|
| 자산 추적 | ✅ 주식, ETF, 암호화폐 | ✅ S&P 500 + 암호화폐 |
| 포트폴리오 최적화 | ❌ 없음 | ✅ 5가지 방법론 |
| 백테스팅 | ❌ 없음 | ✅ 포함 |
| 팩터 분석 | ❌ 없음 | ✅ Fama-French |
| 리스크 분석 | ⚠️ 기본 | ✅ 통합 (Risk Spoke) |
| 세금 최적화 | ❌ 없음 | ✅ TLH 포함 |
| 실시간 데이터 | ✅ | ✅ (7 APIs) |
| MCP 통합 | ❌ | ✅ 독보적 |

**차별점**: Fin-Hub는 **정량적 분석 및 최적화**에 강점, Ghostfolio는 **UI/UX 및 추적**에 강점

---

## 💡 7. 핵심 인사이트

### 7.1 해야 할 것 (Do)

✅ **PyPortfolioOpt 활용**: 검증된 라이브러리, 풍부한 기능
✅ **HRP 구현**: 전통적 MVO의 불안정성 극복
✅ **Risk Spoke 통합**: 이미 구축된 리스크 분석 도구 활용
✅ **S&P 500 데이터 활용**: 충분한 백테스팅 및 분석 가능
✅ **Tax Loss Harvesting**: 2025년 핵심 트렌드, 차별화 요소
✅ **Factor Investing**: 전문 투자자 전략, Fama-French 무료 데이터

### 7.2 하지 말아야 할 것 (Don't)

❌ **처음부터 복잡한 알고리즘 구현**: PyPortfolioOpt 활용
❌ **모든 자산군 지원**: 우선 주식/ETF 집중, 이후 확장
❌ **복잡한 UI 구축**: MCP 도구로 충분, Claude Desktop이 UI
❌ **유료 데이터 API**: 기존 무료 API + 로컬 데이터 최대 활용
❌ **과도한 백테스팅 엔진**: VectorBT 또는 간단한 구현으로 충분

### 7.3 차별화 전략

1. **MCP 생태계 통합**: Market + Risk + Portfolio 완벽 연동
2. **정량적 분석 강화**: 전문가급 최적화 및 팩터 분석
3. **Tax Optimization**: 경쟁자 대부분 없는 기능
4. **API 우선 설계**: Claude Code와의 완벽한 통합

---

## 🚀 8. 실행 계획 (6주)

### Week 1-2: 핵심 기능
- [ ] Portfolio Optimization API (PyPortfolioOpt)
- [ ] Portfolio Rebalancing API
- [ ] Portfolio Performance API
- [ ] MCP 서버 통합
- [ ] 테스트 스위트

### Week 3-4: 고급 분석
- [ ] Backtesting API (VectorBT)
- [ ] Factor Analysis API (Fama-French)
- [ ] Asset Allocation API
- [ ] Market/Risk Spoke 통합
- [ ] 문서화

### Week 5-6: 최적화 및 마무리
- [ ] Tax Optimization API
- [ ] Portfolio Dashboard API
- [ ] 성능 최적화
- [ ] 종합 테스트
- [ ] 사용 가이드 작성

---

## 📚 9. 참고 자료

### Python 라이브러리
- PyPortfolioOpt: https://github.com/robertmartin8/PyPortfolioOpt
- skfolio: https://arxiv.org/abs/2507.04176
- Riskfolio-Lib: https://riskfolio-lib.readthedocs.io/
- VectorBT: https://vectorbt.dev/

### 무료 데이터 소스
- Fama-French Data: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html
- AQR Factors: https://www.aqr.com/Insights/Datasets
- FRED Economic Data: https://fred.stlouisfed.org/

### 학습 자료
- Modern Portfolio Theory: https://www.investopedia.com/terms/m/modernportfoliotheory.asp
- Factor Investing: https://www.cfainstitute.org/en/research/foundation/factor-investing
- Tax Loss Harvesting: https://www.investopedia.com/terms/t/taxgainlossharvesting.asp

---

**결론**: Portfolio Spoke는 **정량적 분석 및 최적화**에 집중하여, 기존 오픈소스 도구(Ghostfolio 등)와 차별화된 **전문가급 포트폴리오 관리 도구**를 MCP 생태계 내에 구축합니다.
