"""
기술지표 베이스 클래스
Jesse AI 패턴을 따른 고성능 지표 계산 기반
"""

import numpy as np
import pandas as pd
from abc import ABC, abstractmethod
from typing import Union, Dict, Any, Optional, List
import numba as nb
from dataclasses import dataclass
import warnings


@dataclass
class IndicatorConfig:
    """지표 설정 데이터클래스"""
    name: str
    period: int
    params: Dict[str, Any]
    source_column: str = 'close'


@dataclass
class IndicatorResult:
    """지표 계산 결과"""
    name: str
    values: np.ndarray
    signals: Optional[np.ndarray] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseIndicator(ABC):
    """기술지표 베이스 클래스"""

    def __init__(self, config: Optional[IndicatorConfig] = None):
        self.config = config or self._get_default_config()
        self.is_calculated = False
        self.result: Optional[IndicatorResult] = None

    @abstractmethod
    def _get_default_config(self) -> IndicatorConfig:
        """기본 설정 반환"""
        pass

    @abstractmethod
    def calculate(self, data: pd.DataFrame) -> IndicatorResult:
        """지표 계산 (서브클래스에서 구현)"""
        pass

    def validate_data(self, data: pd.DataFrame) -> bool:
        """데이터 유효성 검증"""
        required_columns = ['open', 'high', 'low', 'close', 'volume']

        if not all(col in data.columns for col in required_columns):
            missing = [col for col in required_columns if col not in data.columns]
            raise ValueError(f"Missing required columns: {missing}")

        if len(data) < self.config.period:
            raise ValueError(f"Insufficient data. Need {self.config.period}, got {len(data)}")

        return True

    def preprocess_data(self, data: pd.DataFrame) -> np.ndarray:
        """데이터 전처리"""
        if self.config.source_column not in data.columns:
            raise ValueError(f"Source column '{self.config.source_column}' not found")

        return data[self.config.source_column].values

    def generate_signals(self, values: np.ndarray) -> Optional[np.ndarray]:
        """매매 신호 생성 (선택적)"""
        return None

    def get_metadata(self) -> Dict[str, Any]:
        """지표 메타데이터 반환"""
        return {
            'name': self.config.name,
            'period': self.config.period,
            'params': self.config.params,
            'type': self.__class__.__name__
        }


# Numba 최적화된 공통 함수들
@nb.jit(nopython=True, cache=True)
def sma_numba(values: np.ndarray, period: int) -> np.ndarray:
    """Numba 최적화된 단순이동평균"""
    result = np.full(len(values), np.nan)

    for i in range(period - 1, len(values)):
        result[i] = np.mean(values[i - period + 1:i + 1])

    return result


@nb.jit(nopython=True, cache=True)
def ema_numba(values: np.ndarray, period: int) -> np.ndarray:
    """Numba 최적화된 지수이동평균"""
    alpha = 2.0 / (period + 1.0)
    result = np.full(len(values), np.nan)

    # 첫 번째 유효값으로 초기화
    first_valid_idx = 0
    for i in range(len(values)):
        if not np.isnan(values[i]):
            result[i] = values[i]
            first_valid_idx = i
            break

    # EMA 계산
    for i in range(first_valid_idx + 1, len(values)):
        if not np.isnan(values[i]):
            result[i] = alpha * values[i] + (1 - alpha) * result[i - 1]
        else:
            result[i] = result[i - 1]

    return result


@nb.jit(nopython=True, cache=True)
def rsi_numba(values: np.ndarray, period: int) -> np.ndarray:
    """Numba 최적화된 RSI"""
    if len(values) < period + 1:
        return np.full(len(values), np.nan)

    # 가격 변화 계산
    deltas = np.diff(values)
    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)

    result = np.full(len(values), np.nan)

    # 초기 평균 계산
    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])

    if avg_loss == 0:
        result[period] = 100.0
    else:
        rs = avg_gain / avg_loss
        result[period] = 100.0 - (100.0 / (1.0 + rs))

    # 이후 값들 계산 (Wilder's smoothing)
    for i in range(period + 1, len(values)):
        avg_gain = (avg_gain * (period - 1) + gains[i - 1]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i - 1]) / period

        if avg_loss == 0:
            result[i] = 100.0
        else:
            rs = avg_gain / avg_loss
            result[i] = 100.0 - (100.0 / (1.0 + rs))

    return result


@nb.jit(nopython=True, cache=True)
def bollinger_bands_numba(values: np.ndarray, period: int, std_dev: float = 2.0):
    """Numba 최적화된 볼린저 밴드"""
    sma = sma_numba(values, period)

    upper = np.full(len(values), np.nan)
    lower = np.full(len(values), np.nan)

    for i in range(period - 1, len(values)):
        window = values[i - period + 1:i + 1]
        std = np.std(window)

        upper[i] = sma[i] + (std_dev * std)
        lower[i] = sma[i] - (std_dev * std)

    return sma, upper, lower


@nb.jit(nopython=True, cache=True)
def macd_numba(values: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9):
    """Numba 최적화된 MACD"""
    ema_fast = ema_numba(values, fast)
    ema_slow = ema_numba(values, slow)

    macd_line = ema_fast - ema_slow
    signal_line = ema_numba(macd_line, signal)
    histogram = macd_line - signal_line

    return macd_line, signal_line, histogram


@nb.jit(nopython=True, cache=True)
def stochastic_numba(high: np.ndarray, low: np.ndarray, close: np.ndarray,
                    k_period: int = 14, d_period: int = 3):
    """Numba 최적화된 스토캐스틱"""
    k_values = np.full(len(close), np.nan)

    for i in range(k_period - 1, len(close)):
        highest_high = np.max(high[i - k_period + 1:i + 1])
        lowest_low = np.min(low[i - k_period + 1:i + 1])

        if highest_high - lowest_low != 0:
            k_values[i] = 100 * (close[i] - lowest_low) / (highest_high - lowest_low)
        else:
            k_values[i] = 50.0

    d_values = sma_numba(k_values, d_period)

    return k_values, d_values


# 벡터화된 유틸리티 함수들
def true_range(high: np.ndarray, low: np.ndarray, close: np.ndarray) -> np.ndarray:
    """True Range 계산"""
    prev_close = np.roll(close, 1)
    prev_close[0] = close[0]

    tr1 = high - low
    tr2 = np.abs(high - prev_close)
    tr3 = np.abs(low - prev_close)

    return np.maximum(tr1, np.maximum(tr2, tr3))


def typical_price(high: np.ndarray, low: np.ndarray, close: np.ndarray) -> np.ndarray:
    """Typical Price 계산"""
    return (high + low + close) / 3.0


def weighted_close(high: np.ndarray, low: np.ndarray, close: np.ndarray) -> np.ndarray:
    """Weighted Close 계산"""
    return (high + low + 2 * close) / 4.0


class IndicatorBatch:
    """배치 지표 계산을 위한 클래스"""

    def __init__(self, indicators: List[BaseIndicator]):
        self.indicators = indicators

    def calculate_all(self, data: pd.DataFrame) -> Dict[str, IndicatorResult]:
        """모든 지표를 배치로 계산"""
        results = {}

        # 데이터 유효성 검증
        for indicator in self.indicators:
            indicator.validate_data(data)

        # 병렬 계산 (향후 multiprocessing 적용 가능)
        for indicator in self.indicators:
            try:
                result = indicator.calculate(data)
                results[indicator.config.name] = result
            except Exception as e:
                warnings.warn(f"Failed to calculate {indicator.config.name}: {e}")

        return results


class IndicatorCache:
    """지표 결과 캐싱 시스템"""

    def __init__(self, max_size: int = 1000):
        self.cache = {}
        self.max_size = max_size

    def get_key(self, symbol: str, timeframe: str, indicator_name: str,
                start_time: str, end_time: str) -> str:
        """캐시 키 생성"""
        return f"{symbol}:{timeframe}:{indicator_name}:{start_time}:{end_time}"

    def get(self, key: str) -> Optional[IndicatorResult]:
        """캐시에서 결과 조회"""
        return self.cache.get(key)

    def set(self, key: str, result: IndicatorResult):
        """캐시에 결과 저장"""
        if len(self.cache) >= self.max_size:
            # LRU 방식으로 오래된 항목 제거
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]

        self.cache[key] = result

    def clear(self):
        """캐시 초기화"""
        self.cache.clear()