"""
추세 지표 (Trend Indicators)
Jesse AI 스타일 고성능 추세 분석 지표들
"""

import numpy as np
import pandas as pd
import numba as nb
from typing import Optional, Dict, Any, Tuple
from .base import BaseIndicator, IndicatorConfig, IndicatorResult, register_indicator
from .base import sma_numba, ema_numba


@register_indicator("sma")
class SimpleMovingAverage(BaseIndicator):
    """단순이동평균 (SMA)"""

    def _get_default_config(self) -> IndicatorConfig:
        return IndicatorConfig(
            name="sma",
            period=20,
            params={},
            source_column='close'
        )

    def calculate(self, data: pd.DataFrame) -> IndicatorResult:
        self.validate_data(data)
        values = self.preprocess_data(data)

        sma_values = sma_numba(values, self.config.period)

        return IndicatorResult(
            name=self.config.name,
            values=sma_values,
            signals=self.generate_signals(sma_values),
            metadata=self.get_metadata()
        )

    def generate_signals(self, values: np.ndarray) -> Optional[np.ndarray]:
        """가격과 이동평균 교차 신호"""
        signals = np.zeros(len(values))
        # 1: Buy, -1: Sell, 0: Hold
        # 구현 필요시 추가
        return signals


@register_indicator("ema")
class ExponentialMovingAverage(BaseIndicator):
    """지수이동평균 (EMA)"""

    def _get_default_config(self) -> IndicatorConfig:
        return IndicatorConfig(
            name="ema",
            period=20,
            params={},
            source_column='close'
        )

    def calculate(self, data: pd.DataFrame) -> IndicatorResult:
        self.validate_data(data)
        values = self.preprocess_data(data)

        ema_values = ema_numba(values, self.config.period)

        return IndicatorResult(
            name=self.config.name,
            values=ema_values,
            signals=self.generate_signals(ema_values),
            metadata=self.get_metadata()
        )


@register_indicator("wma")
class WeightedMovingAverage(BaseIndicator):
    """가중이동평균 (WMA)"""

    def _get_default_config(self) -> IndicatorConfig:
        return IndicatorConfig(
            name="wma",
            period=20,
            params={},
            source_column='close'
        )

    def calculate(self, data: pd.DataFrame) -> IndicatorResult:
        self.validate_data(data)
        values = self.preprocess_data(data)

        wma_values = self._calculate_wma(values, self.config.period)

        return IndicatorResult(
            name=self.config.name,
            values=wma_values,
            metadata=self.get_metadata()
        )

    @staticmethod
    @nb.jit(nopython=True, cache=True)
    def _calculate_wma(values: np.ndarray, period: int) -> np.ndarray:
        """WMA 계산"""
        result = np.full(len(values), np.nan)
        weights = np.arange(1, period + 1, dtype=np.float64)
        weight_sum = np.sum(weights)

        for i in range(period - 1, len(values)):
            window = values[i - period + 1:i + 1]
            result[i] = np.sum(window * weights) / weight_sum

        return result


@register_indicator("dema")
class DoubleExponentialMovingAverage(BaseIndicator):
    """이중지수이동평균 (DEMA)"""

    def _get_default_config(self) -> IndicatorConfig:
        return IndicatorConfig(
            name="dema",
            period=20,
            params={},
            source_column='close'
        )

    def calculate(self, data: pd.DataFrame) -> IndicatorResult:
        self.validate_data(data)
        values = self.preprocess_data(data)

        dema_values = self._calculate_dema(values, self.config.period)

        return IndicatorResult(
            name=self.config.name,
            values=dema_values,
            metadata=self.get_metadata()
        )

    def _calculate_dema(self, values: np.ndarray, period: int) -> np.ndarray:
        """DEMA 계산: 2 * EMA - EMA(EMA)"""
        ema1 = ema_numba(values, period)
        ema2 = ema_numba(ema1, period)

        return 2 * ema1 - ema2


@register_indicator("tema")
class TripleExponentialMovingAverage(BaseIndicator):
    """삼중지수이동평균 (TEMA)"""

    def _get_default_config(self) -> IndicatorConfig:
        return IndicatorConfig(
            name="tema",
            period=20,
            params={},
            source_column='close'
        )

    def calculate(self, data: pd.DataFrame) -> IndicatorResult:
        self.validate_data(data)
        values = self.preprocess_data(data)

        tema_values = self._calculate_tema(values, self.config.period)

        return IndicatorResult(
            name=self.config.name,
            values=tema_values,
            metadata=self.get_metadata()
        )

    def _calculate_tema(self, values: np.ndarray, period: int) -> np.ndarray:
        """TEMA 계산: 3*EMA - 3*EMA(EMA) + EMA(EMA(EMA))"""
        ema1 = ema_numba(values, period)
        ema2 = ema_numba(ema1, period)
        ema3 = ema_numba(ema2, period)

        return 3 * ema1 - 3 * ema2 + ema3


@register_indicator("kama")
class KaufmanAdaptiveMovingAverage(BaseIndicator):
    """카우프만 적응형 이동평균 (KAMA)"""

    def _get_default_config(self) -> IndicatorConfig:
        return IndicatorConfig(
            name="kama",
            period=14,
            params={'fast_sc': 2, 'slow_sc': 30},
            source_column='close'
        )

    def calculate(self, data: pd.DataFrame) -> IndicatorResult:
        self.validate_data(data)
        values = self.preprocess_data(data)

        kama_values = self._calculate_kama(
            values,
            self.config.period,
            self.config.params['fast_sc'],
            self.config.params['slow_sc']
        )

        return IndicatorResult(
            name=self.config.name,
            values=kama_values,
            metadata=self.get_metadata()
        )

    @staticmethod
    @nb.jit(nopython=True, cache=True)
    def _calculate_kama(values: np.ndarray, period: int, fast_sc: int, slow_sc: int) -> np.ndarray:
        """KAMA 계산"""
        result = np.full(len(values), np.nan)

        if len(values) <= period:
            return result

        # 첫 번째 값 초기화
        result[period] = values[period]

        for i in range(period + 1, len(values)):
            # 변화량 계산
            change = abs(values[i] - values[i - period])

            # 변동성 계산
            volatility = 0.0
            for j in range(period):
                volatility += abs(values[i - j] - values[i - j - 1])

            # 효율성 비율 계산
            if volatility > 0:
                er = change / volatility
            else:
                er = 0.0

            # 스무딩 상수 계산
            fastest_sc = 2.0 / (fast_sc + 1.0)
            slowest_sc = 2.0 / (slow_sc + 1.0)
            sc = (er * (fastest_sc - slowest_sc) + slowest_sc) ** 2

            # KAMA 계산
            result[i] = result[i - 1] + sc * (values[i] - result[i - 1])

        return result


@register_indicator("mama")
class MESAAdaptiveMovingAverage(BaseIndicator):
    """MESA 적응형 이동평균 (MAMA)"""

    def _get_default_config(self) -> IndicatorConfig:
        return IndicatorConfig(
            name="mama",
            period=50,  # 최소 데이터 포인트
            params={'fast_limit': 0.5, 'slow_limit': 0.05},
            source_column='close'
        )

    def calculate(self, data: pd.DataFrame) -> IndicatorResult:
        self.validate_data(data)
        values = self.preprocess_data(data)

        mama_values, fama_values = self._calculate_mama(
            values,
            self.config.params['fast_limit'],
            self.config.params['slow_limit']
        )

        return IndicatorResult(
            name=self.config.name,
            values=mama_values,
            metadata={
                **self.get_metadata(),
                'fama': fama_values.tolist()
            }
        )

    def _calculate_mama(self, values: np.ndarray, fast_limit: float, slow_limit: float) -> Tuple[np.ndarray, np.ndarray]:
        """MESA 적응형 이동평균 계산"""
        length = len(values)
        mama = np.full(length, np.nan)
        fama = np.full(length, np.nan)

        if length < 6:
            return mama, fama

        # 초기값 설정
        mama[5] = values[5]
        fama[5] = values[5]

        # Hilbert Transform를 사용한 위상 계산 (단순화된 버전)
        for i in range(6, length):
            # 단순화된 적응형 팩터 계산
            price_change = abs(values[i] - values[i-1])
            volatility = np.std(values[max(0, i-10):i+1])

            if volatility > 0:
                alpha = min(fast_limit, price_change / volatility)
            else:
                alpha = slow_limit

            alpha = max(alpha, slow_limit)

            mama[i] = alpha * values[i] + (1 - alpha) * mama[i-1]
            fama[i] = 0.5 * alpha * mama[i] + (1 - 0.5 * alpha) * fama[i-1]

        return mama, fama


@register_indicator("trima")
class TriangularMovingAverage(BaseIndicator):
    """삼각 이동평균 (TRIMA)"""

    def _get_default_config(self) -> IndicatorConfig:
        return IndicatorConfig(
            name="trima",
            period=20,
            params={},
            source_column='close'
        )

    def calculate(self, data: pd.DataFrame) -> IndicatorResult:
        self.validate_data(data)
        values = self.preprocess_data(data)

        trima_values = self._calculate_trima(values, self.config.period)

        return IndicatorResult(
            name=self.config.name,
            values=trima_values,
            metadata=self.get_metadata()
        )

    def _calculate_trima(self, values: np.ndarray, period: int) -> np.ndarray:
        """TRIMA 계산: SMA of SMA"""
        if period % 2 == 1:
            # 홀수
            n = (period + 1) // 2
        else:
            # 짝수
            n = period // 2

        sma1 = sma_numba(values, n)
        trima = sma_numba(sma1, n)

        return trima


@register_indicator("vwma")
class VolumeWeightedMovingAverage(BaseIndicator):
    """거래량 가중 이동평균 (VWMA)"""

    def _get_default_config(self) -> IndicatorConfig:
        return IndicatorConfig(
            name="vwma",
            period=20,
            params={},
            source_column='close'
        )

    def calculate(self, data: pd.DataFrame) -> IndicatorResult:
        self.validate_data(data)

        if 'volume' not in data.columns:
            raise ValueError("Volume data required for VWMA")

        close_values = data['close'].values
        volume_values = data['volume'].values

        vwma_values = self._calculate_vwma(close_values, volume_values, self.config.period)

        return IndicatorResult(
            name=self.config.name,
            values=vwma_values,
            metadata=self.get_metadata()
        )

    @staticmethod
    @nb.jit(nopython=True, cache=True)
    def _calculate_vwma(prices: np.ndarray, volumes: np.ndarray, period: int) -> np.ndarray:
        """VWMA 계산"""
        result = np.full(len(prices), np.nan)

        for i in range(period - 1, len(prices)):
            price_volume = 0.0
            total_volume = 0.0

            for j in range(period):
                idx = i - j
                price_volume += prices[idx] * volumes[idx]
                total_volume += volumes[idx]

            if total_volume > 0:
                result[i] = price_volume / total_volume
            else:
                result[i] = prices[i]

        return result