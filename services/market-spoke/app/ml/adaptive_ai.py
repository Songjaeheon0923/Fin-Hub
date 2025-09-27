"""
FreqAI 스타일 적응형 머신러닝 시스템
시장 상황별 자동 전략 조정 및 실시간 성과 피드백 루프
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import logging
import pickle
import json
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# ML 라이브러리
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.svm import SVC, SVR
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import joblib

from ..analysis.multi_timeframe_engine import MultiTimeFrameEngine, TimeFrame
from ..indicators import IndicatorBatch
from ..exchanges.unified_data_fetcher import UnifiedDataFetcher


logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    """시장 레짐"""
    BULL_TREND = "bull_trend"
    BEAR_TREND = "bear_trend"
    SIDEWAYS = "sideways"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    UNCERTAIN = "uncertain"


class ModelType(Enum):
    """모델 타입"""
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    CLUSTERING = "clustering"


@dataclass
class MLFeatures:
    """ML 특성 데이터"""
    technical_indicators: Dict[str, float]
    price_features: Dict[str, float]
    volume_features: Dict[str, float]
    volatility_features: Dict[str, float]
    market_features: Dict[str, float]
    timestamp: datetime


@dataclass
class ModelPerformance:
    """모델 성능 지표"""
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    mse: float
    mae: float
    r2_score: float
    last_updated: datetime
    sample_count: int


@dataclass
class AdaptiveConfig:
    """적응형 AI 설정"""
    symbol: str
    model_types: List[ModelType] = field(default_factory=lambda: [ModelType.CLASSIFICATION])
    retrain_interval_hours: int = 24
    min_samples_for_training: int = 100
    performance_threshold: float = 0.6
    regime_detection_period: int = 50
    feature_importance_threshold: float = 0.05
    enable_online_learning: bool = True
    max_models_per_regime: int = 3


class FeatureEngineer:
    """특성 엔지니어링"""

    def __init__(self):
        self.scalers: Dict[str, Any] = {}
        self.feature_names: List[str] = []

    def extract_features(self, data: pd.DataFrame,
                        indicator_results: Dict[str, Any]) -> MLFeatures:
        """데이터에서 특성 추출"""
        if data.empty:
            return self._create_empty_features()

        # 가격 특성
        price_features = self._extract_price_features(data)

        # 거래량 특성
        volume_features = self._extract_volume_features(data)

        # 변동성 특성
        volatility_features = self._extract_volatility_features(data)

        # 기술지표 특성
        technical_indicators = self._extract_indicator_features(indicator_results)

        # 시장 특성
        market_features = self._extract_market_features(data)

        return MLFeatures(
            technical_indicators=technical_indicators,
            price_features=price_features,
            volume_features=volume_features,
            volatility_features=volatility_features,
            market_features=market_features,
            timestamp=datetime.now()
        )

    def _extract_price_features(self, data: pd.DataFrame) -> Dict[str, float]:
        """가격 관련 특성 추출"""
        features = {}

        if len(data) < 2:
            return features

        try:
            close = data['close'].values
            high = data['high'].values
            low = data['low'].values
            open_price = data['open'].values

            # 가격 변화율
            features['price_change_1d'] = (close[-1] - close[-2]) / close[-2] if len(close) > 1 else 0
            features['price_change_7d'] = (close[-1] - close[-8]) / close[-8] if len(close) > 7 else 0
            features['price_change_30d'] = (close[-1] - close[-31]) / close[-31] if len(close) > 30 else 0

            # 고가/저가 대비 현재가 위치
            if len(data) >= 20:
                high_20 = np.max(high[-20:])
                low_20 = np.min(low[-20:])
                if high_20 != low_20:
                    features['price_position_20d'] = (close[-1] - low_20) / (high_20 - low_20)

            # 캔들 패턴
            if len(data) >= 3:
                body_size = abs(close[-1] - open_price[-1])
                candle_range = high[-1] - low[-1]
                features['body_to_range_ratio'] = body_size / candle_range if candle_range > 0 else 0

                # 상승/하락 캔들
                features['is_bullish_candle'] = 1.0 if close[-1] > open_price[-1] else 0.0

            # 갭
            if len(data) >= 2:
                gap = (open_price[-1] - close[-2]) / close[-2]
                features['gap_percent'] = gap

        except Exception as e:
            logger.warning(f"Error extracting price features: {e}")

        return features

    def _extract_volume_features(self, data: pd.DataFrame) -> Dict[str, float]:
        """거래량 관련 특성 추출"""
        features = {}

        if 'volume' not in data.columns or len(data) < 2:
            return features

        try:
            volume = data['volume'].values
            close = data['close'].values

            # 거래량 변화율
            features['volume_change_1d'] = (volume[-1] - volume[-2]) / volume[-2] if volume[-2] > 0 else 0

            # 평균 거래량 대비
            if len(volume) >= 20:
                avg_volume_20 = np.mean(volume[-20:])
                features['volume_vs_avg_20d'] = volume[-1] / avg_volume_20 if avg_volume_20 > 0 else 1

            # 가격-거래량 관계
            if len(data) >= 10:
                price_change = np.diff(close[-10:])
                volume_ratio = volume[-9:] / np.mean(volume[-20:]) if len(volume) >= 20 else volume[-9:]

                # 상승시 거래량 vs 하락시 거래량
                up_volume = np.mean(volume_ratio[price_change > 0]) if np.any(price_change > 0) else 0
                down_volume = np.mean(volume_ratio[price_change < 0]) if np.any(price_change < 0) else 0

                features['up_volume_avg'] = up_volume
                features['down_volume_avg'] = down_volume

        except Exception as e:
            logger.warning(f"Error extracting volume features: {e}")

        return features

    def _extract_volatility_features(self, data: pd.DataFrame) -> Dict[str, float]:
        """변동성 관련 특성 추출"""
        features = {}

        try:
            close = data['close'].values
            high = data['high'].values
            low = data['low'].values

            # 단순 변동성 (수익률 표준편차)
            if len(close) >= 20:
                returns = np.diff(np.log(close[-20:]))
                features['volatility_20d'] = np.std(returns) * np.sqrt(252)  # 연환산

            # True Range 기반 변동성
            if len(data) >= 14:
                prev_close = np.roll(close, 1)
                prev_close[0] = close[0]

                tr = np.maximum(high - low,
                               np.maximum(np.abs(high - prev_close),
                                        np.abs(low - prev_close)))

                atr_14 = np.mean(tr[-14:])
                features['atr_14'] = atr_14

                # ATR 대비 현재 변동성
                current_tr = tr[-1]
                features['current_tr_vs_atr'] = current_tr / atr_14 if atr_14 > 0 else 1

            # 변동성 클러스터링
            if len(close) >= 30:
                returns = np.diff(np.log(close[-30:]))
                vol_short = np.std(returns[-5:])  # 5일 변동성
                vol_long = np.std(returns[-20:])  # 20일 변동성
                features['vol_short_vs_long'] = vol_short / vol_long if vol_long > 0 else 1

        except Exception as e:
            logger.warning(f"Error extracting volatility features: {e}")

        return features

    def _extract_indicator_features(self, indicator_results: Dict[str, Any]) -> Dict[str, float]:
        """기술지표 특성 추출"""
        features = {}

        try:
            for name, result in indicator_results.items():
                if hasattr(result, 'values') and result.values is not None:
                    values = result.values
                    if len(values) > 0 and not np.isnan(values[-1]):
                        features[f'{name}_current'] = float(values[-1])

                        # 지표의 변화율
                        if len(values) >= 2 and not np.isnan(values[-2]):
                            change = (values[-1] - values[-2]) / abs(values[-2]) if values[-2] != 0 else 0
                            features[f'{name}_change'] = change

                        # 지표의 트렌드 (최근 5일)
                        if len(values) >= 5:
                            recent_values = values[-5:]
                            valid_values = [v for v in recent_values if not np.isnan(v)]
                            if len(valid_values) >= 3:
                                slope = np.polyfit(range(len(valid_values)), valid_values, 1)[0]
                                features[f'{name}_trend'] = slope

                # 추가 메타데이터에서 특성 추출
                if hasattr(result, 'metadata') and result.metadata:
                    for key, value in result.metadata.items():
                        if isinstance(value, (int, float)) and not np.isnan(value):
                            features[f'{name}_{key}'] = float(value)

        except Exception as e:
            logger.warning(f"Error extracting indicator features: {e}")

        return features

    def _extract_market_features(self, data: pd.DataFrame) -> Dict[str, float]:
        """시장 관련 특성 추출"""
        features = {}

        try:
            # 시간 특성
            if not data.empty:
                latest_time = data.index[-1] if hasattr(data.index[-1], 'hour') else datetime.now()
                if hasattr(latest_time, 'hour'):
                    features['hour_of_day'] = latest_time.hour
                    features['day_of_week'] = latest_time.weekday()

            # 시장 상태
            close = data['close'].values
            if len(close) >= 50:
                # 트렌드 강도
                sma_20 = np.mean(close[-20:])
                sma_50 = np.mean(close[-50:])
                features['trend_strength'] = (sma_20 - sma_50) / sma_50 if sma_50 > 0 else 0

                # 모멘텀
                momentum_10 = (close[-1] - close[-11]) / close[-11] if len(close) > 10 else 0
                features['momentum_10d'] = momentum_10

        except Exception as e:
            logger.warning(f"Error extracting market features: {e}")

        return features

    def _create_empty_features(self) -> MLFeatures:
        """빈 특성 객체 생성"""
        return MLFeatures(
            technical_indicators={},
            price_features={},
            volume_features={},
            volatility_features={},
            market_features={},
            timestamp=datetime.now()
        )

    def features_to_array(self, features: MLFeatures) -> np.ndarray:
        """특성을 배열로 변환"""
        all_features = {}
        all_features.update(features.technical_indicators)
        all_features.update(features.price_features)
        all_features.update(features.volume_features)
        all_features.update(features.volatility_features)
        all_features.update(features.market_features)

        # 특성 이름 순서 고정
        if not self.feature_names:
            self.feature_names = sorted(all_features.keys())

        # 배열 생성
        feature_array = []
        for name in self.feature_names:
            value = all_features.get(name, 0.0)
            feature_array.append(float(value))

        return np.array(feature_array).reshape(1, -1)


class RegimeDetector:
    """시장 레짐 탐지기"""

    def __init__(self, period: int = 50):
        self.period = period

    def detect_regime(self, data: pd.DataFrame) -> MarketRegime:
        """현재 시장 레짐 탐지"""
        if len(data) < self.period:
            return MarketRegime.UNCERTAIN

        try:
            close = data['close'].values
            high = data['high'].values
            low = data['low'].values

            # 트렌드 분석
            recent_close = close[-self.period:]
            trend_slope = np.polyfit(range(len(recent_close)), recent_close, 1)[0]
            trend_strength = abs(trend_slope) / np.mean(recent_close)

            # 변동성 분석
            returns = np.diff(np.log(close[-self.period:]))
            volatility = np.std(returns) * np.sqrt(252)

            # 레짐 결정
            if volatility > 0.5:  # 50% 이상 연변동성
                return MarketRegime.HIGH_VOLATILITY
            elif volatility < 0.15:  # 15% 미만 연변동성
                return MarketRegime.LOW_VOLATILITY
            elif trend_strength > 0.002:  # 강한 트렌드
                if trend_slope > 0:
                    return MarketRegime.BULL_TREND
                else:
                    return MarketRegime.BEAR_TREND
            else:
                return MarketRegime.SIDEWAYS

        except Exception as e:
            logger.error(f"Error detecting regime: {e}")
            return MarketRegime.UNCERTAIN


class AdaptiveMLModel:
    """적응형 ML 모델"""

    def __init__(self, model_type: ModelType, regime: MarketRegime):
        self.model_type = model_type
        self.regime = regime
        self.model = None
        self.scaler = None
        self.performance = None
        self.last_trained = None
        self.sample_count = 0

        self._initialize_model()

    def _initialize_model(self):
        """모델 초기화"""
        if self.model_type == ModelType.CLASSIFICATION:
            # 앙상블 모델 사용
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42
            )
        elif self.model_type == ModelType.REGRESSION:
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42
            )

        self.scaler = RobustScaler()  # 이상값에 강한 스케일러

    def train(self, X: np.ndarray, y: np.ndarray) -> ModelPerformance:
        """모델 훈련"""
        try:
            if len(X) < 10:  # 최소 샘플 수
                raise ValueError("Insufficient training samples")

            # 데이터 스케일링
            X_scaled = self.scaler.fit_transform(X)

            # 훈련/검증 분할
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y, test_size=0.2, random_state=42, stratify=y if self.model_type == ModelType.CLASSIFICATION else None
            )

            # 모델 훈련
            self.model.fit(X_train, y_train)

            # 성능 평가
            y_pred = self.model.predict(X_test)

            if self.model_type == ModelType.CLASSIFICATION:
                performance = ModelPerformance(
                    accuracy=accuracy_score(y_test, y_pred),
                    precision=precision_score(y_test, y_pred, average='weighted', zero_division=0),
                    recall=recall_score(y_test, y_pred, average='weighted', zero_division=0),
                    f1_score=f1_score(y_test, y_pred, average='weighted', zero_division=0),
                    mse=0.0,
                    mae=0.0,
                    r2_score=0.0,
                    last_updated=datetime.now(),
                    sample_count=len(X)
                )
            else:
                performance = ModelPerformance(
                    accuracy=0.0,
                    precision=0.0,
                    recall=0.0,
                    f1_score=0.0,
                    mse=mean_squared_error(y_test, y_pred),
                    mae=mean_absolute_error(y_test, y_pred),
                    r2_score=r2_score(y_test, y_pred),
                    last_updated=datetime.now(),
                    sample_count=len(X)
                )

            self.performance = performance
            self.last_trained = datetime.now()
            self.sample_count = len(X)

            logger.info(f"Model trained for {self.regime.value}: {performance}")
            return performance

        except Exception as e:
            logger.error(f"Error training model: {e}")
            raise

    def predict(self, X: np.ndarray) -> Tuple[Union[int, float], float]:
        """예측 수행"""
        if self.model is None or self.scaler is None:
            raise ValueError("Model not trained")

        try:
            X_scaled = self.scaler.transform(X)
            prediction = self.model.predict(X_scaled)[0]

            # 신뢰도 계산 (확률 기반)
            if hasattr(self.model, 'predict_proba'):
                probabilities = self.model.predict_proba(X_scaled)[0]
                confidence = np.max(probabilities)
            else:
                # 회귀의 경우 기본 신뢰도
                confidence = 0.7

            return prediction, confidence

        except Exception as e:
            logger.error(f"Error making prediction: {e}")
            return 0, 0.0

    def save(self, filepath: Path):
        """모델 저장"""
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'model_type': self.model_type,
            'regime': self.regime,
            'performance': self.performance,
            'last_trained': self.last_trained,
            'sample_count': self.sample_count
        }
        joblib.dump(model_data, filepath)

    @classmethod
    def load(cls, filepath: Path):
        """모델 로드"""
        model_data = joblib.load(filepath)

        instance = cls(model_data['model_type'], model_data['regime'])
        instance.model = model_data['model']
        instance.scaler = model_data['scaler']
        instance.performance = model_data['performance']
        instance.last_trained = model_data['last_trained']
        instance.sample_count = model_data['sample_count']

        return instance


class AdaptiveAIEngine:
    """적응형 AI 엔진"""

    def __init__(self, config: AdaptiveConfig, data_fetcher: UnifiedDataFetcher):
        self.config = config
        self.data_fetcher = data_fetcher
        self.feature_engineer = FeatureEngineer()
        self.regime_detector = RegimeDetector(config.regime_detection_period)

        # 레짐별 모델 저장소
        self.models: Dict[MarketRegime, Dict[ModelType, AdaptiveMLModel]] = {}

        # 훈련 데이터 버퍼
        self.training_buffer: List[Tuple[MLFeatures, Any]] = []
        self.max_buffer_size = 10000

        # 성능 추적
        self.performance_history: List[Dict] = []

        # 모델 저장 경로
        self.model_dir = Path(f"models/{config.symbol}")
        self.model_dir.mkdir(parents=True, exist_ok=True)

    async def initialize(self):
        """AI 엔진 초기화"""
        logger.info(f"Initializing Adaptive AI Engine for {self.config.symbol}")

        # 기존 모델 로드
        await self._load_existing_models()

        # 초기 데이터 수집 및 훈련
        await self._initial_training()

    async def _load_existing_models(self):
        """기존 모델 로드"""
        for regime in MarketRegime:
            for model_type in self.config.model_types:
                model_file = self.model_dir / f"{regime.value}_{model_type.value}.joblib"
                if model_file.exists():
                    try:
                        model = AdaptiveMLModel.load(model_file)
                        if regime not in self.models:
                            self.models[regime] = {}
                        self.models[regime][model_type] = model
                        logger.info(f"Loaded model: {regime.value}_{model_type.value}")
                    except Exception as e:
                        logger.error(f"Error loading model {model_file}: {e}")

    async def _initial_training(self):
        """초기 훈련 데이터 수집 및 모델 훈련"""
        try:
            # 과거 데이터 수집 (최근 3개월)
            since = datetime.now() - timedelta(days=90)

            from ..exchanges.unified_data_fetcher import DataRequest
            data_request = DataRequest(
                symbol=self.config.symbol,
                timeframe="1h",
                since=since,
                limit=2000,
                require_validation=False
            )

            market_data = await self.data_fetcher.fetch_historical_data(data_request)

            if not market_data.data.empty:
                await self._process_historical_data(market_data.data)

        except Exception as e:
            logger.error(f"Error in initial training: {e}")

    async def _process_historical_data(self, data: pd.DataFrame):
        """과거 데이터 처리 및 훈련 데이터 생성"""
        if len(data) < 100:
            return

        # 지표 계산
        from ..indicators import get_indicator
        indicators = []
        for indicator_name in ["sma", "ema", "rsi", "macd", "stoch"]:
            try:
                indicator = get_indicator(indicator_name)
                indicators.append(indicator)
            except:
                continue

        if not indicators:
            return

        indicator_batch = IndicatorBatch(indicators)
        indicator_results = indicator_batch.calculate_all(data)

        # 슬라이딩 윈도우로 특성 추출
        window_size = 50
        for i in range(window_size, len(data)):
            window_data = data.iloc[i-window_size:i]
            features = self.feature_engineer.extract_features(window_data, indicator_results)

            # 타겟 생성 (다음 시간의 가격 방향)
            if i < len(data) - 1:
                current_price = data['close'].iloc[i]
                next_price = data['close'].iloc[i + 1]
                target = 1 if next_price > current_price else 0

                self.training_buffer.append((features, target))

        # 버퍼 크기 관리
        if len(self.training_buffer) > self.max_buffer_size:
            self.training_buffer = self.training_buffer[-self.max_buffer_size:]

        # 모델 훈련
        await self._retrain_models()

    async def _retrain_models(self):
        """모델 재훈련"""
        if len(self.training_buffer) < self.config.min_samples_for_training:
            logger.warning(f"Insufficient training samples: {len(self.training_buffer)}")
            return

        # 특성과 타겟 분리
        X_list = []
        y_list = []

        for features, target in self.training_buffer:
            feature_array = self.feature_engineer.features_to_array(features)
            X_list.append(feature_array[0])
            y_list.append(target)

        X = np.array(X_list)
        y = np.array(y_list)

        # 레짐별로 모델 훈련
        for regime in MarketRegime:
            for model_type in self.config.model_types:
                try:
                    # 모델 생성 또는 기존 모델 사용
                    if regime not in self.models:
                        self.models[regime] = {}

                    if model_type not in self.models[regime]:
                        self.models[regime][model_type] = AdaptiveMLModel(model_type, regime)

                    model = self.models[regime][model_type]

                    # 모델 훈련
                    performance = model.train(X, y)

                    # 모델 저장
                    model_file = self.model_dir / f"{regime.value}_{model_type.value}.joblib"
                    model.save(model_file)

                    logger.info(f"Retrained model {regime.value}_{model_type.value}: "
                              f"Accuracy={performance.accuracy:.3f}")

                except Exception as e:
                    logger.error(f"Error retraining model {regime.value}_{model_type.value}: {e}")

    async def predict(self, current_data: pd.DataFrame) -> Dict[str, Any]:
        """현재 데이터로 예측"""
        try:
            # 현재 시장 레짐 탐지
            current_regime = self.regime_detector.detect_regime(current_data)

            # 특성 추출
            from ..indicators import get_indicator
            indicators = []
            for indicator_name in ["sma", "ema", "rsi", "macd", "stoch"]:
                try:
                    indicator = get_indicator(indicator_name)
                    indicators.append(indicator)
                except:
                    continue

            if not indicators:
                return {"error": "No indicators available"}

            indicator_batch = IndicatorBatch(indicators)
            indicator_results = indicator_batch.calculate_all(current_data)

            features = self.feature_engineer.extract_features(current_data, indicator_results)
            feature_array = self.feature_engineer.features_to_array(features)

            # 예측 수행
            predictions = {}

            if current_regime in self.models:
                for model_type, model in self.models[current_regime].items():
                    try:
                        prediction, confidence = model.predict(feature_array)
                        predictions[model_type.value] = {
                            'prediction': prediction,
                            'confidence': confidence,
                            'model_performance': model.performance.__dict__ if model.performance else None
                        }
                    except Exception as e:
                        logger.error(f"Error in prediction: {e}")

            return {
                'regime': current_regime.value,
                'predictions': predictions,
                'features_count': len(self.feature_engineer.feature_names),
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error in predict: {e}")
            return {"error": str(e)}

    async def update_with_feedback(self, actual_result: Any):
        """실제 결과로 피드백 업데이트"""
        # 온라인 학습 구현 (간단한 버퍼 업데이트)
        if self.config.enable_online_learning and self.training_buffer:
            # 최신 특성에 실제 결과 추가
            latest_features = self.training_buffer[-1][0] if self.training_buffer else None
            if latest_features:
                self.training_buffer.append((latest_features, actual_result))

                # 주기적 재훈련 체크
                await self._check_retrain_schedule()

    async def _check_retrain_schedule(self):
        """재훈련 스케줄 확인"""
        for regime_models in self.models.values():
            for model in regime_models.values():
                if model.last_trained:
                    hours_since_training = (datetime.now() - model.last_trained).total_seconds() / 3600
                    if hours_since_training >= self.config.retrain_interval_hours:
                        await self._retrain_models()
                        break

    def get_model_status(self) -> Dict[str, Any]:
        """모델 상태 조회"""
        status = {
            'symbol': self.config.symbol,
            'total_models': 0,
            'training_samples': len(self.training_buffer),
            'regimes': {}
        }

        for regime, models in self.models.items():
            regime_info = {
                'model_count': len(models),
                'models': {}
            }

            for model_type, model in models.items():
                model_info = {
                    'last_trained': model.last_trained.isoformat() if model.last_trained else None,
                    'sample_count': model.sample_count,
                    'performance': model.performance.__dict__ if model.performance else None
                }
                regime_info['models'][model_type.value] = model_info
                status['total_models'] += 1

            status['regimes'][regime.value] = regime_info

        return status


# 전역 적응형 AI 엔진 관리
_adaptive_engines: Dict[str, AdaptiveAIEngine] = {}


async def get_adaptive_ai_engine(symbol: str, data_fetcher: UnifiedDataFetcher) -> AdaptiveAIEngine:
    """적응형 AI 엔진 반환"""
    global _adaptive_engines

    if symbol not in _adaptive_engines:
        config = AdaptiveConfig(symbol=symbol)
        engine = AdaptiveAIEngine(config, data_fetcher)
        await engine.initialize()
        _adaptive_engines[symbol] = engine

    return _adaptive_engines[symbol]