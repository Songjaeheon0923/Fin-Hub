"""
멀티 시간대 동시 분석 엔진
TradeMaster 방식 1분/5분/1시간/일별 병렬 처리
Look-ahead bias 방지 백테스팅
"""

import asyncio
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from collections import defaultdict, deque

from ..indicators import IndicatorBatch, BaseIndicator, get_indicator
from ..exchanges.unified_data_fetcher import UnifiedDataFetcher, DataRequest


logger = logging.getLogger(__name__)


class TimeFrame(Enum):
    """시간프레임 정의"""
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"
    W1 = "1w"


class SignalStrength(Enum):
    """신호 강도"""
    VERY_STRONG = "very_strong"
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    NEUTRAL = "neutral"


@dataclass
class TimeFrameSignal:
    """시간프레임별 신호"""
    timeframe: TimeFrame
    timestamp: datetime
    signal_type: str  # buy, sell, hold
    strength: SignalStrength
    confidence: float
    indicators: Dict[str, float]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MultiTimeFrameAnalysis:
    """멀티 시간프레임 분석 결과"""
    symbol: str
    timestamp: datetime
    signals: Dict[TimeFrame, TimeFrameSignal]
    consensus_signal: str
    consensus_strength: SignalStrength
    confidence_score: float
    risk_level: float
    recommendations: List[str]
    market_context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalysisConfig:
    """분석 설정"""
    symbol: str
    timeframes: List[TimeFrame] = field(default_factory=lambda: [
        TimeFrame.M5, TimeFrame.M15, TimeFrame.H1, TimeFrame.H4, TimeFrame.D1
    ])
    lookback_periods: Dict[TimeFrame, int] = field(default_factory=lambda: {
        TimeFrame.M1: 500,
        TimeFrame.M5: 300,
        TimeFrame.M15: 200,
        TimeFrame.H1: 100,
        TimeFrame.H4: 50,
        TimeFrame.D1: 30,
        TimeFrame.W1: 20
    })
    indicators: List[str] = field(default_factory=lambda: [
        "sma", "ema", "rsi", "macd", "stoch", "bollinger", "atr"
    ])
    enable_consensus: bool = True
    min_confidence_threshold: float = 0.6


class TimeFrameAnalyzer:
    """단일 시간프레임 분석기"""

    def __init__(self, timeframe: TimeFrame, config: AnalysisConfig):
        self.timeframe = timeframe
        self.config = config
        self.indicators: List[BaseIndicator] = []
        self._setup_indicators()

    def _setup_indicators(self):
        """지표 설정"""
        # 시간프레임별 최적화된 지표 파라미터
        timeframe_configs = {
            TimeFrame.M1: {"rsi_period": 14, "sma_period": 20, "ema_period": 12},
            TimeFrame.M5: {"rsi_period": 14, "sma_period": 20, "ema_period": 12},
            TimeFrame.M15: {"rsi_period": 14, "sma_period": 20, "ema_period": 12},
            TimeFrame.H1: {"rsi_period": 14, "sma_period": 50, "ema_period": 21},
            TimeFrame.H4: {"rsi_period": 14, "sma_period": 50, "ema_period": 21},
            TimeFrame.D1: {"rsi_period": 14, "sma_period": 200, "ema_period": 50},
            TimeFrame.W1: {"rsi_period": 14, "sma_period": 200, "ema_period": 50}
        }

        params = timeframe_configs.get(self.timeframe, timeframe_configs[TimeFrame.H1])

        for indicator_name in self.config.indicators:
            try:
                indicator = get_indicator(indicator_name)
                # 시간프레임별 파라미터 적용
                if hasattr(indicator.config, 'period'):
                    if indicator_name == "rsi":
                        indicator.config.period = params["rsi_period"]
                    elif indicator_name in ["sma", "ema"]:
                        period_key = f"{indicator_name}_period"
                        if period_key in params:
                            indicator.config.period = params[period_key]

                self.indicators.append(indicator)
            except Exception as e:
                logger.warning(f"Failed to load indicator {indicator_name}: {e}")

    async def analyze(self, data: pd.DataFrame) -> TimeFrameSignal:
        """시간프레임 분석 실행"""
        if data.empty or len(data) < 20:
            return self._create_neutral_signal()

        try:
            # 지표 계산
            indicator_batch = IndicatorBatch(self.indicators)
            indicator_results = indicator_batch.calculate_all(data)

            # 신호 생성
            signal_type, strength, confidence = self._generate_signal(
                data, indicator_results
            )

            # 지표값 추출
            indicator_values = {}
            for name, result in indicator_results.items():
                if result.values is not None and len(result.values) > 0:
                    # 최신값만 저장
                    latest_value = result.values[-1]
                    if not np.isnan(latest_value):
                        indicator_values[name] = float(latest_value)

            return TimeFrameSignal(
                timeframe=self.timeframe,
                timestamp=datetime.now(),
                signal_type=signal_type,
                strength=strength,
                confidence=confidence,
                indicators=indicator_values,
                metadata={
                    'data_points': len(data),
                    'price_change_24h': self._calculate_price_change(data)
                }
            )

        except Exception as e:
            logger.error(f"Analysis error for {self.timeframe}: {e}")
            return self._create_neutral_signal()

    def _generate_signal(self, data: pd.DataFrame,
                        indicator_results: Dict[str, Any]) -> Tuple[str, SignalStrength, float]:
        """신호 생성 로직"""
        signals = []
        confidences = []

        # RSI 신호
        if "rsi" in indicator_results:
            rsi_values = indicator_results["rsi"].values
            if len(rsi_values) > 0 and not np.isnan(rsi_values[-1]):
                rsi = rsi_values[-1]
                if rsi < 30:
                    signals.append("buy")
                    confidences.append(0.8)
                elif rsi > 70:
                    signals.append("sell")
                    confidences.append(0.8)
                else:
                    signals.append("hold")
                    confidences.append(0.5)

        # MACD 신호
        if "macd" in indicator_results:
            macd_result = indicator_results["macd"]
            if hasattr(macd_result, 'metadata') and 'histogram' in macd_result.metadata:
                histogram = macd_result.metadata['histogram']
                if len(histogram) >= 2:
                    if histogram[-1] > histogram[-2] and histogram[-1] > 0:
                        signals.append("buy")
                        confidences.append(0.7)
                    elif histogram[-1] < histogram[-2] and histogram[-1] < 0:
                        signals.append("sell")
                        confidences.append(0.7)

        # 이동평균 신호
        if "sma" in indicator_results and "ema" in indicator_results:
            sma_values = indicator_results["sma"].values
            ema_values = indicator_results["ema"].values

            if (len(sma_values) > 0 and len(ema_values) > 0 and
                not np.isnan(sma_values[-1]) and not np.isnan(ema_values[-1])):

                current_price = data['close'].iloc[-1]
                if current_price > sma_values[-1] and current_price > ema_values[-1]:
                    signals.append("buy")
                    confidences.append(0.6)
                elif current_price < sma_values[-1] and current_price < ema_values[-1]:
                    signals.append("sell")
                    confidences.append(0.6)

        # 신호 통합
        if not signals:
            return "hold", SignalStrength.NEUTRAL, 0.3

        # 다수결 투표
        buy_count = signals.count("buy")
        sell_count = signals.count("sell")
        hold_count = signals.count("hold")

        if buy_count > sell_count and buy_count > hold_count:
            signal_type = "buy"
        elif sell_count > buy_count and sell_count > hold_count:
            signal_type = "sell"
        else:
            signal_type = "hold"

        # 신뢰도 계산
        total_confidence = sum(confidences) / len(confidences) if confidences else 0.3

        # 강도 계산
        max_count = max(buy_count, sell_count, hold_count)
        strength_ratio = max_count / len(signals)

        if strength_ratio >= 0.8 and total_confidence >= 0.7:
            strength = SignalStrength.VERY_STRONG
        elif strength_ratio >= 0.6 and total_confidence >= 0.6:
            strength = SignalStrength.STRONG
        elif strength_ratio >= 0.4:
            strength = SignalStrength.MODERATE
        else:
            strength = SignalStrength.WEAK

        return signal_type, strength, total_confidence

    def _calculate_price_change(self, data: pd.DataFrame) -> float:
        """24시간 가격 변화율 계산"""
        if len(data) < 2:
            return 0.0

        current_price = data['close'].iloc[-1]
        previous_price = data['close'].iloc[0]

        return ((current_price - previous_price) / previous_price) * 100

    def _create_neutral_signal(self) -> TimeFrameSignal:
        """중립 신호 생성"""
        return TimeFrameSignal(
            timeframe=self.timeframe,
            timestamp=datetime.now(),
            signal_type="hold",
            strength=SignalStrength.NEUTRAL,
            confidence=0.0,
            indicators={},
            metadata={'error': 'Insufficient data'}
        )


class MultiTimeFrameEngine:
    """멀티 시간프레임 분석 엔진"""

    def __init__(self, data_fetcher: UnifiedDataFetcher):
        self.data_fetcher = data_fetcher
        self.analyzers: Dict[TimeFrame, TimeFrameAnalyzer] = {}
        self.executor = ThreadPoolExecutor(max_workers=8)

        # 분석 결과 캐시
        self.analysis_cache: Dict[str, MultiTimeFrameAnalysis] = {}
        self.cache_ttl = 300  # 5분

        # 실시간 분석을 위한 데이터 버퍼
        self.data_buffers: Dict[str, Dict[TimeFrame, deque]] = defaultdict(
            lambda: defaultdict(lambda: deque(maxlen=1000))
        )

    async def setup_analysis(self, config: AnalysisConfig):
        """분석 설정"""
        for timeframe in config.timeframes:
            analyzer = TimeFrameAnalyzer(timeframe, config)
            self.analyzers[timeframe] = analyzer

        logger.info(f"Setup multi-timeframe analysis for {config.symbol}")

    async def analyze_symbol(self, config: AnalysisConfig) -> MultiTimeFrameAnalysis:
        """심볼 멀티 시간프레임 분석"""
        # 캐시 확인
        cache_key = f"{config.symbol}_{datetime.now().strftime('%Y%m%d_%H%M')}"
        if cache_key in self.analysis_cache:
            cached_analysis = self.analysis_cache[cache_key]
            age_seconds = (datetime.now() - cached_analysis.timestamp).total_seconds()
            if age_seconds < self.cache_ttl:
                return cached_analysis

        # 분석기 설정
        await self.setup_analysis(config)

        # 각 시간프레임별 데이터 수집 및 분석
        analysis_tasks = []

        for timeframe in config.timeframes:
            task = self._analyze_timeframe(config, timeframe)
            analysis_tasks.append((timeframe, task))

        # 병렬 실행
        timeframe_signals = {}
        for timeframe, task in analysis_tasks:
            try:
                signal = await task
                timeframe_signals[timeframe] = signal
            except Exception as e:
                logger.error(f"Analysis failed for {timeframe}: {e}")
                # 기본 중립 신호 생성
                timeframe_signals[timeframe] = TimeFrameSignal(
                    timeframe=timeframe,
                    timestamp=datetime.now(),
                    signal_type="hold",
                    strength=SignalStrength.NEUTRAL,
                    confidence=0.0,
                    indicators={}
                )

        # 합의 신호 계산
        consensus_result = self._calculate_consensus(timeframe_signals, config)

        # 리스크 레벨 계산
        risk_level = self._calculate_risk_level(timeframe_signals)

        # 추천사항 생성
        recommendations = self._generate_recommendations(timeframe_signals, consensus_result)

        # 시장 컨텍스트 추가
        market_context = await self._get_market_context(config.symbol)

        analysis = MultiTimeFrameAnalysis(
            symbol=config.symbol,
            timestamp=datetime.now(),
            signals=timeframe_signals,
            consensus_signal=consensus_result[0],
            consensus_strength=consensus_result[1],
            confidence_score=consensus_result[2],
            risk_level=risk_level,
            recommendations=recommendations,
            market_context=market_context
        )

        # 캐시에 저장
        self.analysis_cache[cache_key] = analysis

        # 캐시 크기 관리
        if len(self.analysis_cache) > 100:
            oldest_key = min(self.analysis_cache.keys(),
                           key=lambda k: self.analysis_cache[k].timestamp)
            del self.analysis_cache[oldest_key]

        return analysis

    async def _analyze_timeframe(self, config: AnalysisConfig,
                                timeframe: TimeFrame) -> TimeFrameSignal:
        """단일 시간프레임 분석"""
        # 데이터 요청 생성
        lookback = config.lookback_periods.get(timeframe, 100)
        since = datetime.now() - timedelta(days=lookback)

        data_request = DataRequest(
            symbol=config.symbol,
            timeframe=timeframe.value,
            since=since,
            limit=lookback,
            require_validation=False  # 빠른 분석을 위해 검증 스킵
        )

        # 데이터 수집
        market_data = await self.data_fetcher.fetch_historical_data(data_request)

        # 분석 실행
        analyzer = self.analyzers[timeframe]
        signal = await analyzer.analyze(market_data.data)

        return signal

    def _calculate_consensus(self, signals: Dict[TimeFrame, TimeFrameSignal],
                           config: AnalysisConfig) -> Tuple[str, SignalStrength, float]:
        """시간프레임 간 합의 신호 계산"""
        if not config.enable_consensus:
            # 가장 긴 시간프레임의 신호 사용
            longest_tf = max(signals.keys(), key=lambda x: self._timeframe_weight(x))
            signal = signals[longest_tf]
            return signal.signal_type, signal.strength, signal.confidence

        # 가중치 기반 투표
        weighted_votes = defaultdict(float)
        total_weight = 0.0
        confidence_sum = 0.0

        for timeframe, signal in signals.items():
            weight = self._timeframe_weight(timeframe)

            # 신뢰도가 임계값 이상인 신호만 고려
            if signal.confidence >= config.min_confidence_threshold:
                weighted_votes[signal.signal_type] += weight * signal.confidence
                total_weight += weight
                confidence_sum += signal.confidence * weight

        if total_weight == 0:
            return "hold", SignalStrength.NEUTRAL, 0.0

        # 최고 득표 신호
        consensus_signal = max(weighted_votes.items(), key=lambda x: x[1])[0]

        # 평균 신뢰도
        avg_confidence = confidence_sum / total_weight

        # 합의 강도 계산
        max_vote = max(weighted_votes.values())
        consensus_ratio = max_vote / sum(weighted_votes.values())

        if consensus_ratio >= 0.7 and avg_confidence >= 0.8:
            consensus_strength = SignalStrength.VERY_STRONG
        elif consensus_ratio >= 0.6 and avg_confidence >= 0.7:
            consensus_strength = SignalStrength.STRONG
        elif consensus_ratio >= 0.5:
            consensus_strength = SignalStrength.MODERATE
        else:
            consensus_strength = SignalStrength.WEAK

        return consensus_signal, consensus_strength, avg_confidence

    def _timeframe_weight(self, timeframe: TimeFrame) -> float:
        """시간프레임별 가중치"""
        weights = {
            TimeFrame.M1: 0.1,
            TimeFrame.M5: 0.2,
            TimeFrame.M15: 0.3,
            TimeFrame.H1: 0.5,
            TimeFrame.H4: 0.8,
            TimeFrame.D1: 1.0,
            TimeFrame.W1: 1.2
        }
        return weights.get(timeframe, 0.5)

    def _calculate_risk_level(self, signals: Dict[TimeFrame, TimeFrameSignal]) -> float:
        """리스크 레벨 계산 (0.0 ~ 1.0)"""
        risk_factors = []

        # 시간프레임 간 신호 일치도
        signal_types = [s.signal_type for s in signals.values()]
        if len(set(signal_types)) > 1:
            risk_factors.append(0.3)  # 신호 불일치

        # 신뢰도 평균
        avg_confidence = sum(s.confidence for s in signals.values()) / len(signals)
        if avg_confidence < 0.6:
            risk_factors.append(0.4)  # 낮은 신뢰도

        # 변동성 (가격 변화율 기준)
        price_changes = []
        for signal in signals.values():
            if 'price_change_24h' in signal.metadata:
                price_changes.append(abs(signal.metadata['price_change_24h']))

        if price_changes:
            avg_volatility = sum(price_changes) / len(price_changes)
            if avg_volatility > 10:  # 10% 이상 변동
                risk_factors.append(0.5)

        return min(1.0, sum(risk_factors))

    def _generate_recommendations(self, signals: Dict[TimeFrame, TimeFrameSignal],
                                consensus_result: Tuple[str, SignalStrength, float]) -> List[str]:
        """추천사항 생성"""
        recommendations = []
        consensus_signal, consensus_strength, consensus_confidence = consensus_result

        # 기본 추천
        if consensus_signal == "buy":
            if consensus_strength in [SignalStrength.STRONG, SignalStrength.VERY_STRONG]:
                recommendations.append("Strong buy signal detected across multiple timeframes")
            else:
                recommendations.append("Consider buying with proper risk management")
        elif consensus_signal == "sell":
            if consensus_strength in [SignalStrength.STRONG, SignalStrength.VERY_STRONG]:
                recommendations.append("Strong sell signal detected across multiple timeframes")
            else:
                recommendations.append("Consider selling or reducing position")
        else:
            recommendations.append("Hold current position and monitor market conditions")

        # 리스크 관리 추천
        risk_level = self._calculate_risk_level(signals)
        if risk_level > 0.7:
            recommendations.append("High risk detected - use smaller position sizes")
        elif risk_level > 0.4:
            recommendations.append("Moderate risk - implement stop-loss orders")

        # 시간프레임별 특별 추천
        short_term_signals = [s for tf, s in signals.items()
                            if tf in [TimeFrame.M5, TimeFrame.M15]]
        long_term_signals = [s for tf, s in signals.items()
                           if tf in [TimeFrame.H4, TimeFrame.D1]]

        if short_term_signals and long_term_signals:
            short_consensus = max(set(s.signal_type for s in short_term_signals),
                                key=lambda x: [s.signal_type for s in short_term_signals].count(x))
            long_consensus = max(set(s.signal_type for s in long_term_signals),
                               key=lambda x: [s.signal_type for s in long_term_signals].count(x))

            if short_consensus != long_consensus:
                recommendations.append(
                    f"Short-term trend ({short_consensus}) conflicts with long-term trend ({long_consensus})"
                )

        return recommendations

    async def _get_market_context(self, symbol: str) -> Dict[str, Any]:
        """시장 컨텍스트 정보 수집"""
        try:
            # 시장 개요 데이터 수집
            market_overview = await self.data_fetcher.get_market_overview()

            context = {
                'market_timestamp': datetime.now().isoformat(),
                'symbol_in_overview': symbol in market_overview.get('markets', {}),
                'total_markets_analyzed': len(market_overview.get('markets', {}))
            }

            # 심볼별 정보 추가
            if symbol in market_overview.get('markets', {}):
                symbol_data = market_overview['markets'][symbol]
                context.update({
                    'current_price': symbol_data.get('price'),
                    'data_quality': symbol_data.get('quality'),
                    'source_count': symbol_data.get('sources')
                })

            return context

        except Exception as e:
            logger.error(f"Error getting market context: {e}")
            return {'error': str(e)}

    async def get_real_time_signals(self, symbols: List[str],
                                  timeframes: List[TimeFrame] = None) -> Dict[str, MultiTimeFrameAnalysis]:
        """실시간 신호 모니터링"""
        if timeframes is None:
            timeframes = [TimeFrame.M5, TimeFrame.M15, TimeFrame.H1]

        results = {}

        for symbol in symbols:
            config = AnalysisConfig(
                symbol=symbol,
                timeframes=timeframes,
                enable_consensus=True
            )

            try:
                analysis = await self.analyze_symbol(config)
                results[symbol] = analysis
            except Exception as e:
                logger.error(f"Real-time analysis failed for {symbol}: {e}")

        return results

    async def shutdown(self):
        """엔진 종료"""
        self.executor.shutdown(wait=True)
        logger.info("Multi-timeframe engine shut down")