"""
모멘텀 지표 (Momentum Indicators)
Jesse AI 스타일 고성능 모멘텀 분석 지표들
"""

import numpy as np
import pandas as pd
import numba as nb
from typing import Optional, Dict, Any, Tuple
from .base import BaseIndicator, IndicatorConfig, IndicatorResult, register_indicator
from .base import sma_numba, ema_numba, rsi_numba, macd_numba, stochastic_numba


@register_indicator("rsi")
class RelativeStrengthIndex(BaseIndicator):
    """상대강도지수 (RSI)"""

    def _get_default_config(self) -> IndicatorConfig:
        return IndicatorConfig(
            name="rsi",
            period=14,
            params={'overbought': 70, 'oversold': 30},
            source_column='close'
        )

    def calculate(self, data: pd.DataFrame) -> IndicatorResult:
        self.validate_data(data)
        values = self.preprocess_data(data)

        rsi_values = rsi_numba(values, self.config.period)
        signals = self.generate_signals(rsi_values)

        return IndicatorResult(
            name=self.config.name,
            values=rsi_values,
            signals=signals,
            metadata=self.get_metadata()
        )

    def generate_signals(self, values: np.ndarray) -> Optional[np.ndarray]:
        """RSI 과매수/과매도 신호"""
        signals = np.zeros(len(values))
        overbought = self.config.params['overbought']
        oversold = self.config.params['oversold']

        # 과매도에서 벗어날 때 매수 신호
        signals[1:] = np.where(
            (values[:-1] <= oversold) & (values[1:] > oversold), 1, 0
        )
        # 과매수에서 벗어날 때 매도 신호
        signals[1:] = np.where(
            (values[:-1] >= overbought) & (values[1:] < overbought), -1, signals[1:]
        )

        return signals


@register_indicator("macd")
class MACD(BaseIndicator):
    """이동평균수렴확산지수 (MACD)"""

    def _get_default_config(self) -> IndicatorConfig:
        return IndicatorConfig(
            name="macd",
            period=26,  # slow period
            params={'fast': 12, 'slow': 26, 'signal': 9},
            source_column='close'
        )

    def calculate(self, data: pd.DataFrame) -> IndicatorResult:
        self.validate_data(data)
        values = self.preprocess_data(data)

        macd_line, signal_line, histogram = macd_numba(
            values,
            self.config.params['fast'],
            self.config.params['slow'],
            self.config.params['signal']
        )

        signals = self.generate_signals(macd_line, signal_line, histogram)

        return IndicatorResult(
            name=self.config.name,
            values=macd_line,
            signals=signals,
            metadata={
                **self.get_metadata(),
                'signal_line': signal_line.tolist(),
                'histogram': histogram.tolist()
            }
        )

    def generate_signals(self, macd_line: np.ndarray, signal_line: np.ndarray,
                        histogram: np.ndarray) -> Optional[np.ndarray]:
        """MACD 신호"""
        signals = np.zeros(len(macd_line))

        # MACD가 시그널을 상향 돌파하면 매수
        for i in range(1, len(macd_line)):
            if (macd_line[i-1] <= signal_line[i-1] and
                macd_line[i] > signal_line[i] and
                not np.isnan(macd_line[i]) and not np.isnan(signal_line[i])):
                signals[i] = 1
            # MACD가 시그널을 하향 돌파하면 매도
            elif (macd_line[i-1] >= signal_line[i-1] and
                  macd_line[i] < signal_line[i] and
                  not np.isnan(macd_line[i]) and not np.isnan(signal_line[i])):
                signals[i] = -1

        return signals


@register_indicator("stoch")
class StochasticOscillator(BaseIndicator):
    """스토캐스틱 (Stochastic)"""

    def _get_default_config(self) -> IndicatorConfig:
        return IndicatorConfig(
            name="stoch",
            period=14,
            params={'k_period': 14, 'd_period': 3, 'overbought': 80, 'oversold': 20},
            source_column='close'
        )

    def calculate(self, data: pd.DataFrame) -> IndicatorResult:
        self.validate_data(data)

        if not all(col in data.columns for col in ['high', 'low', 'close']):
            raise ValueError("High, Low, Close data required for Stochastic")

        high = data['high'].values
        low = data['low'].values
        close = data['close'].values

        k_values, d_values = stochastic_numba(
            high, low, close,
            self.config.params['k_period'],
            self.config.params['d_period']
        )

        signals = self.generate_signals(k_values, d_values)

        return IndicatorResult(
            name=self.config.name,
            values=k_values,
            signals=signals,
            metadata={
                **self.get_metadata(),
                'd_values': d_values.tolist()
            }
        )

    def generate_signals(self, k_values: np.ndarray, d_values: np.ndarray) -> Optional[np.ndarray]:
        """스토캐스틱 신호"""
        signals = np.zeros(len(k_values))
        overbought = self.config.params['overbought']
        oversold = self.config.params['oversold']

        for i in range(1, len(k_values)):
            # %K가 %D를 상향 돌파하고 과매도 영역에서 벗어날 때
            if (k_values[i-1] <= d_values[i-1] and k_values[i] > d_values[i] and
                k_values[i] > oversold and not np.isnan(k_values[i])):
                signals[i] = 1
            # %K가 %D를 하향 돌파하고 과매수 영역에서 벗어날 때
            elif (k_values[i-1] >= d_values[i-1] and k_values[i] < d_values[i] and
                  k_values[i] < overbought and not np.isnan(k_values[i])):
                signals[i] = -1

        return signals


@register_indicator("williams_r")
class WilliamsR(BaseIndicator):
    """윌리엄스 %R (Williams %R)"""

    def _get_default_config(self) -> IndicatorConfig:
        return IndicatorConfig(
            name="williams_r",
            period=14,
            params={'overbought': -20, 'oversold': -80},
            source_column='close'
        )

    def calculate(self, data: pd.DataFrame) -> IndicatorResult:
        self.validate_data(data)

        if not all(col in data.columns for col in ['high', 'low', 'close']):
            raise ValueError("High, Low, Close data required for Williams %R")

        high = data['high'].values
        low = data['low'].values
        close = data['close'].values

        williams_values = self._calculate_williams_r(high, low, close, self.config.period)
        signals = self.generate_signals(williams_values)

        return IndicatorResult(
            name=self.config.name,
            values=williams_values,
            signals=signals,
            metadata=self.get_metadata()
        )

    @staticmethod
    @nb.jit(nopython=True, cache=True)
    def _calculate_williams_r(high: np.ndarray, low: np.ndarray, close: np.ndarray,
                             period: int) -> np.ndarray:
        """Williams %R 계산"""
        result = np.full(len(close), np.nan)

        for i in range(period - 1, len(close)):
            highest_high = np.max(high[i - period + 1:i + 1])
            lowest_low = np.min(low[i - period + 1:i + 1])

            if highest_high - lowest_low != 0:
                result[i] = -100 * (highest_high - close[i]) / (highest_high - lowest_low)
            else:
                result[i] = -50.0

        return result

    def generate_signals(self, values: np.ndarray) -> Optional[np.ndarray]:
        """Williams %R 신호"""
        signals = np.zeros(len(values))
        overbought = self.config.params['overbought']
        oversold = self.config.params['oversold']

        for i in range(1, len(values)):
            if values[i-1] <= oversold and values[i] > oversold:
                signals[i] = 1
            elif values[i-1] >= overbought and values[i] < overbought:
                signals[i] = -1

        return signals


@register_indicator("cci")
class CommodityChannelIndex(BaseIndicator):
    """상품채널지수 (CCI)"""

    def _get_default_config(self) -> IndicatorConfig:
        return IndicatorConfig(
            name="cci",
            period=20,
            params={'overbought': 100, 'oversold': -100},
            source_column='close'
        )

    def calculate(self, data: pd.DataFrame) -> IndicatorResult:
        self.validate_data(data)

        if not all(col in data.columns for col in ['high', 'low', 'close']):
            raise ValueError("High, Low, Close data required for CCI")

        high = data['high'].values
        low = data['low'].values
        close = data['close'].values

        cci_values = self._calculate_cci(high, low, close, self.config.period)
        signals = self.generate_signals(cci_values)

        return IndicatorResult(
            name=self.config.name,
            values=cci_values,
            signals=signals,
            metadata=self.get_metadata()
        )

    @staticmethod
    @nb.jit(nopython=True, cache=True)
    def _calculate_cci(high: np.ndarray, low: np.ndarray, close: np.ndarray,
                      period: int) -> np.ndarray:
        """CCI 계산"""
        typical_price = (high + low + close) / 3.0
        result = np.full(len(close), np.nan)

        for i in range(period - 1, len(close)):
            tp_window = typical_price[i - period + 1:i + 1]
            sma_tp = np.mean(tp_window)

            # Mean Deviation 계산
            mean_deviation = np.mean(np.abs(tp_window - sma_tp))

            if mean_deviation != 0:
                result[i] = (typical_price[i] - sma_tp) / (0.015 * mean_deviation)
            else:
                result[i] = 0.0

        return result

    def generate_signals(self, values: np.ndarray) -> Optional[np.ndarray]:
        """CCI 신호"""
        signals = np.zeros(len(values))
        overbought = self.config.params['overbought']
        oversold = self.config.params['oversold']

        for i in range(1, len(values)):
            if values[i-1] <= oversold and values[i] > oversold:
                signals[i] = 1
            elif values[i-1] >= overbought and values[i] < overbought:
                signals[i] = -1

        return signals


@register_indicator("roc")
class RateOfChange(BaseIndicator):
    """변화율 (Rate of Change)"""

    def _get_default_config(self) -> IndicatorConfig:
        return IndicatorConfig(
            name="roc",
            period=10,
            params={'threshold': 5.0},
            source_column='close'
        )

    def calculate(self, data: pd.DataFrame) -> IndicatorResult:
        self.validate_data(data)
        values = self.preprocess_data(data)

        roc_values = self._calculate_roc(values, self.config.period)
        signals = self.generate_signals(roc_values)

        return IndicatorResult(
            name=self.config.name,
            values=roc_values,
            signals=signals,
            metadata=self.get_metadata()
        )

    @staticmethod
    @nb.jit(nopython=True, cache=True)
    def _calculate_roc(values: np.ndarray, period: int) -> np.ndarray:
        """ROC 계산"""
        result = np.full(len(values), np.nan)

        for i in range(period, len(values)):
            if values[i - period] != 0:
                result[i] = ((values[i] - values[i - period]) / values[i - period]) * 100
            else:
                result[i] = 0.0

        return result

    def generate_signals(self, values: np.ndarray) -> Optional[np.ndarray]:
        """ROC 신호"""
        signals = np.zeros(len(values))
        threshold = self.config.params['threshold']

        for i in range(1, len(values)):
            if values[i-1] <= -threshold and values[i] > -threshold:
                signals[i] = 1
            elif values[i-1] >= threshold and values[i] < threshold:
                signals[i] = -1

        return signals


@register_indicator("momentum")
class MomentumIndicator(BaseIndicator):
    """모멘텀 지표"""

    def _get_default_config(self) -> IndicatorConfig:
        return IndicatorConfig(
            name="momentum",
            period=10,
            params={},
            source_column='close'
        )

    def calculate(self, data: pd.DataFrame) -> IndicatorResult:
        self.validate_data(data)
        values = self.preprocess_data(data)

        momentum_values = self._calculate_momentum(values, self.config.period)

        return IndicatorResult(
            name=self.config.name,
            values=momentum_values,
            metadata=self.get_metadata()
        )

    @staticmethod
    @nb.jit(nopython=True, cache=True)
    def _calculate_momentum(values: np.ndarray, period: int) -> np.ndarray:
        """모멘텀 계산"""
        result = np.full(len(values), np.nan)

        for i in range(period, len(values)):
            result[i] = values[i] - values[i - period]

        return result


@register_indicator("ppo")
class PercentagePriceOscillator(BaseIndicator):
    """퍼센트 가격 오실레이터 (PPO)"""

    def _get_default_config(self) -> IndicatorConfig:
        return IndicatorConfig(
            name="ppo",
            period=26,
            params={'fast': 12, 'slow': 26, 'signal': 9},
            source_column='close'
        )

    def calculate(self, data: pd.DataFrame) -> IndicatorResult:
        self.validate_data(data)
        values = self.preprocess_data(data)

        ppo_values, signal_line = self._calculate_ppo(
            values,
            self.config.params['fast'],
            self.config.params['slow'],
            self.config.params['signal']
        )

        return IndicatorResult(
            name=self.config.name,
            values=ppo_values,
            metadata={
                **self.get_metadata(),
                'signal_line': signal_line.tolist()
            }
        )

    def _calculate_ppo(self, values: np.ndarray, fast: int, slow: int, signal: int):
        """PPO 계산"""
        ema_fast = ema_numba(values, fast)
        ema_slow = ema_numba(values, slow)

        # PPO = ((EMA_fast - EMA_slow) / EMA_slow) * 100
        ppo = np.where(ema_slow != 0, ((ema_fast - ema_slow) / ema_slow) * 100, 0)
        signal_line = ema_numba(ppo, signal)

        return ppo, signal_line


@register_indicator("ultimate")
class UltimateOscillator(BaseIndicator):
    """얼티메이트 오실레이터 (Ultimate Oscillator)"""

    def _get_default_config(self) -> IndicatorConfig:
        return IndicatorConfig(
            name="ultimate",
            period=28,  # max period
            params={'short': 7, 'medium': 14, 'long': 28},
            source_column='close'
        )

    def calculate(self, data: pd.DataFrame) -> IndicatorResult:
        self.validate_data(data)

        if not all(col in data.columns for col in ['high', 'low', 'close']):
            raise ValueError("High, Low, Close data required for Ultimate Oscillator")

        high = data['high'].values
        low = data['low'].values
        close = data['close'].values

        ultimate_values = self._calculate_ultimate_oscillator(
            high, low, close,
            self.config.params['short'],
            self.config.params['medium'],
            self.config.params['long']
        )

        return IndicatorResult(
            name=self.config.name,
            values=ultimate_values,
            metadata=self.get_metadata()
        )

    def _calculate_ultimate_oscillator(self, high: np.ndarray, low: np.ndarray,
                                     close: np.ndarray, short: int, medium: int, long: int):
        """Ultimate Oscillator 계산"""
        # True Range와 Buying Pressure 계산
        prev_close = np.roll(close, 1)
        prev_close[0] = close[0]

        tr = np.maximum(high - low,
                       np.maximum(np.abs(high - prev_close),
                                np.abs(low - prev_close)))

        bp = close - np.minimum(low, prev_close)

        # 각 기간별 평균값 계산
        def rolling_sum(arr, period):
            result = np.full(len(arr), np.nan)
            for i in range(period - 1, len(arr)):
                result[i] = np.sum(arr[i - period + 1:i + 1])
            return result

        bp_short = rolling_sum(bp, short)
        tr_short = rolling_sum(tr, short)
        bp_medium = rolling_sum(bp, medium)
        tr_medium = rolling_sum(tr, medium)
        bp_long = rolling_sum(bp, long)
        tr_long = rolling_sum(tr, long)

        # Ultimate Oscillator 계산
        uo = 100 * ((4 * bp_short / tr_short) +
                    (2 * bp_medium / tr_medium) +
                    (bp_long / tr_long)) / (4 + 2 + 1)

        return uo