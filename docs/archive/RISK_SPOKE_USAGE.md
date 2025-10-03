# Risk Spoke 사용 가이드

Risk Spoke는 정량적 리스크 관리를 위한 3개의 핵심 도구를 제공합니다.

## 도구 목록

### 1. VaR Calculator (risk.calculate_var)
**설명**: Value at Risk 계산 (Historical, Parametric, Monte Carlo 방법)

**사용 예시:**
```
/mcp use fin-hub-risk

AAPL의 VaR를 계산해줘. 95% 신뢰수준, 포트폴리오 가치 $10,000로 모든 방법 사용
```

**파라미터:**
- `symbol`: 주식 심볼 (예: AAPL, TSLA)
- `method`: "historical", "parametric", "monte_carlo", "all" (기본값: "all")
- `confidence_level`: 신뢰 수준 (기본값: 0.95)
- `time_horizon`: 시간 범위 (일 단위, 기본값: 1)
- `portfolio_value`: 포트폴리오 가치 (기본값: 10000)
- `period`: 역사적 데이터 기간 (기본값: 252일)
- `simulations`: 몬테카를로 시뮬레이션 횟수 (기본값: 10000)

**결과 포함:**
- 각 방법별 VaR (USD 및 %)
- CVaR (Conditional VaR / Expected Shortfall)
- 정규성 검정 (Parametric 방법)
- 리스크 백분위수 (Monte Carlo)
- 방법 간 비교 및 권장사항

---

### 2. Risk Metrics Calculator (risk.calculate_metrics)
**설명**: 포괄적인 리스크 및 성과 지표 계산

**사용 예시:**
```
/mcp use fin-hub-risk

MSFT의 모든 리스크 지표를 252일 기준으로 계산해줘
```

**파라미터:**
- `symbol`: 주식 심볼
- `benchmark`: 벤치마크 심볼 (Beta/Alpha 계산용, 기본값: SPY)
- `period`: 분석 기간 (일 단위, 기본값: 252)
- `risk_free_rate`: 무위험 이자율 (기본값: 0.04 = 4%)
- `metrics`: 계산할 지표 배열 또는 ["all"]

**사용 가능한 지표:**
- `sharpe`: Sharpe Ratio (위험 조정 수익률)
- `sortino`: Sortino Ratio (하방 위험만 고려)
- `drawdown`: Maximum Drawdown (최대 낙폭)
- `volatility`: 변동성 (일간 및 연간)
- `returns`: 수익률 (총, 연환산, 기간별)
- `beta`: 베타 (시장 민감도)
- `alpha`: 알파 (초과 수익)
- `information_ratio`: Information Ratio
- `calmar`: Calmar Ratio (수익률 / 최대낙폭)
- `downside_deviation`: 하방 편차

**결과 포함:**
- 각 지표의 값 및 해석
- 리스크 수준 평가
- 수익 품질 평가
- 맞춤형 권장사항

---

### 3. Portfolio Risk Analyzer (risk.analyze_portfolio)
**설명**: 다중 자산 포트폴리오의 리스크 분석

**사용 예시:**
```
/mcp use fin-hub-risk

다음 포트폴리오를 분석해줘:
- AAPL: 40%
- MSFT: 30%
- GOOGL: 30%
```

**파라미터:**
- `portfolio`: 배열 [{symbol, weight}, ...] (가중치 합 = 1.0)
- `period`: 분석 기간 (기본값: 252)
- `confidence_level`: VaR 신뢰수준 (기본값: 0.95)
- `risk_free_rate`: 무위험 이자율 (기본값: 0.04)
- `rebalance`: 정기 리밸런싱 여부 (기본값: false)

**결과 포함:**

**수익률 지표:**
- 총 수익률 및 연환산 수익률
- 자산별 기여도

**리스크 지표:**
- 포트폴리오 변동성
- 분산 효과 (Diversification Benefit)
- 변동성 감소율

**VaR 분석:**
- Historical VaR
- Parametric VaR
- CVaR (Expected Shortfall)

**분산투자 지표:**
- 평균 상관계수
- Diversification Ratio
- 유효 자산 수 (Effective N)

**상관관계 분석:**
- 상관계수 행렬 통계
- 최고/최저 상관관계 쌍
- 고상관 자산 경고

**성과 지표:**
- Sharpe Ratio
- Sortino Ratio
- Calmar Ratio
- Maximum Drawdown

**집중도 리스크:**
- Herfindahl Index (HHI)
- Top 3/5 집중도
- 최대 포지션 목록

---

## 사용 팁

### 1. VaR 분석 워크플로우
```
1. 단일 자산 VaR 계산 (모든 방법)
2. 방법 간 비교로 일관성 확인
3. 정규성 검정으로 Parametric VaR 타당성 평가
4. 보수적 추정치 선택 (가장 큰 VaR)
```

### 2. 포트폴리오 최적화
```
1. 현재 포트폴리오 분석
2. 상관관계 분석으로 분산효과 확인
3. 집중도 리스크 평가
4. Sharpe Ratio 및 Diversification Ratio 개선 방법 검토
```

### 3. 리스크 모니터링
```
1. 정기적 VaR 업데이트 (주간/월간)
2. Maximum Drawdown 추적
3. 변동성 변화 모니터링
4. Sharpe/Sortino Ratio 추세 분석
```

---

## 테스트 결과

**테스트 성공률:** 90.9% (11개 중 10개 통과)

**검증된 기능:**
- ✅ VaR Calculator: 3가지 방법 모두 정상 작동
- ✅ Risk Metrics: Sharpe, Sortino, Drawdown, Volatility, Returns
- ✅ Portfolio Risk: 2~5 자산 포트폴리오 분석
- ✅ 분산투자 효과 계산
- ✅ 집중도 리스크 분석
- ✅ 포트폴리오 VaR

**알려진 제한사항:**
- Beta/Alpha: 벤치마크 데이터 가용성에 따라 계산 가능 여부 결정
- S&P 500 개별 종목만 지원 (503개)
- 최소 30일 이상의 데이터 필요

---

## 예제: 전체 리스크 분석

```
/mcp use fin-hub-risk

1. 먼저 AAPL의 VaR를 계산해줘 (95% 신뢰수준, $50,000 포트폴리오)
2. AAPL의 모든 리스크 지표를 계산해줘
3. 다음 포트폴리오를 분석해줘:
   - AAPL: 40%
   - MSFT: 30%
   - GOOGL: 20%
   - NVDA: 10%
```

---

**버전:** 1.0.0
**마지막 업데이트:** 2025-10-04
**MCP 서버:** fin-hub-risk
**도구 수:** 3개
