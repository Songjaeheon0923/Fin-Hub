"""
다중소스 데이터 검증 시스템
Awesome Quant 방식 2개 이상 API 교차 검증
"""

import asyncio
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import statistics
import logging
from abc import ABC, abstractmethod


logger = logging.getLogger(__name__)


class DataQuality(Enum):
    """데이터 품질 등급"""
    EXCELLENT = "excellent"    # 95%+ 일치, 3개 이상 소스
    GOOD = "good"             # 90%+ 일치, 2개 이상 소스
    FAIR = "fair"             # 80%+ 일치, 2개 소스
    POOR = "poor"             # 80% 미만 일치
    INSUFFICIENT = "insufficient"  # 1개 소스만 가능


@dataclass
class DataPoint:
    """단일 데이터 포인트"""
    value: float
    timestamp: datetime
    source: str
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """검증 결과"""
    consensus_value: float
    quality: DataQuality
    confidence_score: float
    source_count: int
    outliers: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    raw_values: Dict[str, float] = field(default_factory=dict)
    statistics: Dict[str, float] = field(default_factory=dict)


@dataclass
class SourceConfig:
    """데이터 소스 설정"""
    name: str
    weight: float = 1.0
    timeout_seconds: int = 30
    max_retries: int = 3
    trust_score: float = 1.0  # 0.0 ~ 1.0
    enabled: bool = True


class DataValidator:
    """다중소스 데이터 검증 엔진"""

    def __init__(self):
        self.sources: Dict[str, SourceConfig] = {}
        self.validation_history: List[ValidationResult] = []
        self.source_reliability: Dict[str, float] = {}

        # 이상값 탐지 파라미터
        self.outlier_threshold = 2.5  # 표준편차 기준
        self.min_sources = 2
        self.consensus_threshold = 0.05  # 5% 이내 차이

    def register_source(self, config: SourceConfig):
        """데이터 소스 등록"""
        self.sources[config.name] = config
        if config.name not in self.source_reliability:
            self.source_reliability[config.name] = config.trust_score

        logger.info(f"Registered data source: {config.name}")

    async def validate_price_data(self, symbol: str, data_points: List[DataPoint]) -> ValidationResult:
        """가격 데이터 검증"""
        if len(data_points) < self.min_sources:
            return ValidationResult(
                consensus_value=data_points[0].value if data_points else 0.0,
                quality=DataQuality.INSUFFICIENT,
                confidence_score=0.3,
                source_count=len(data_points),
                warnings=[f"Insufficient sources: {len(data_points)} < {self.min_sources}"]
            )

        # 1. 이상값 탐지
        outliers = self._detect_outliers(data_points)

        # 2. 필터링된 데이터로 합의값 계산
        filtered_points = [dp for dp in data_points if dp.source not in outliers]

        if len(filtered_points) < self.min_sources:
            # 이상값 제거 후 소스가 부족하면 원본 데이터 사용
            filtered_points = data_points
            outliers = []

        # 3. 가중 평균으로 합의값 계산
        consensus_value = self._calculate_weighted_consensus(filtered_points)

        # 4. 품질 평가
        quality = self._assess_data_quality(filtered_points, consensus_value)

        # 5. 신뢰도 점수 계산
        confidence_score = self._calculate_confidence_score(filtered_points, consensus_value, outliers)

        # 6. 통계 계산
        statistics = self._calculate_statistics(filtered_points)

        # 7. 경고 메시지 생성
        warnings = self._generate_warnings(filtered_points, outliers, consensus_value)

        result = ValidationResult(
            consensus_value=consensus_value,
            quality=quality,
            confidence_score=confidence_score,
            source_count=len(filtered_points),
            outliers=outliers,
            warnings=warnings,
            raw_values={dp.source: dp.value for dp in data_points},
            statistics=statistics
        )

        # 검증 기록 저장
        self.validation_history.append(result)
        if len(self.validation_history) > 1000:
            self.validation_history = self.validation_history[-500:]  # 메모리 관리

        # 소스 신뢰도 업데이트
        self._update_source_reliability(data_points, consensus_value, outliers)

        return result

    def _detect_outliers(self, data_points: List[DataPoint]) -> List[str]:
        """이상값 탐지 (Z-Score 방식)"""
        if len(data_points) < 3:
            return []

        values = [dp.value for dp in data_points]
        mean_val = statistics.mean(values)
        std_val = statistics.stdev(values) if len(values) > 1 else 0

        if std_val == 0:
            return []

        outliers = []
        for dp in data_points:
            z_score = abs((dp.value - mean_val) / std_val)
            if z_score > self.outlier_threshold:
                outliers.append(dp.source)

        return outliers

    def _calculate_weighted_consensus(self, data_points: List[DataPoint]) -> float:
        """가중 평균 합의값 계산"""
        if not data_points:
            return 0.0

        total_weight = 0.0
        weighted_sum = 0.0

        for dp in data_points:
            source_config = self.sources.get(dp.source)
            source_weight = source_config.weight if source_config else 1.0
            reliability = self.source_reliability.get(dp.source, 1.0)

            # 최종 가중치 = 설정된 가중치 × 신뢰도 × 데이터 신뢰도
            final_weight = source_weight * reliability * dp.confidence

            weighted_sum += dp.value * final_weight
            total_weight += final_weight

        return weighted_sum / total_weight if total_weight > 0 else statistics.mean([dp.value for dp in data_points])

    def _assess_data_quality(self, data_points: List[DataPoint], consensus_value: float) -> DataQuality:
        """데이터 품질 평가"""
        if len(data_points) < 2:
            return DataQuality.INSUFFICIENT

        # 합의값과의 차이 비율 계산
        deviations = []
        for dp in data_points:
            if consensus_value != 0:
                deviation = abs((dp.value - consensus_value) / consensus_value)
                deviations.append(deviation)

        if not deviations:
            return DataQuality.INSUFFICIENT

        avg_deviation = statistics.mean(deviations)
        max_deviation = max(deviations)

        # 품질 기준
        if len(data_points) >= 3 and avg_deviation <= 0.02 and max_deviation <= 0.05:
            return DataQuality.EXCELLENT
        elif len(data_points) >= 2 and avg_deviation <= 0.05 and max_deviation <= 0.10:
            return DataQuality.GOOD
        elif avg_deviation <= 0.10:
            return DataQuality.FAIR
        else:
            return DataQuality.POOR

    def _calculate_confidence_score(self, data_points: List[DataPoint],
                                  consensus_value: float, outliers: List[str]) -> float:
        """신뢰도 점수 계산 (0.0 ~ 1.0)"""
        if not data_points:
            return 0.0

        base_score = min(len(data_points) / 5.0, 1.0)  # 소스 수 기준

        # 일치도 점수
        deviations = []
        for dp in data_points:
            if consensus_value != 0:
                deviation = abs((dp.value - consensus_value) / consensus_value)
                deviations.append(deviation)

        if deviations:
            consistency_score = max(0, 1 - statistics.mean(deviations) * 10)
        else:
            consistency_score = 0.5

        # 이상값 페널티
        outlier_penalty = len(outliers) * 0.1

        # 소스 신뢰도 가중 평균
        reliability_scores = []
        for dp in data_points:
            reliability = self.source_reliability.get(dp.source, 0.5)
            reliability_scores.append(reliability)

        avg_reliability = statistics.mean(reliability_scores) if reliability_scores else 0.5

        # 최종 점수 계산
        final_score = (base_score * 0.3 + consistency_score * 0.4 +
                      avg_reliability * 0.3) - outlier_penalty

        return max(0.0, min(1.0, final_score))

    def _calculate_statistics(self, data_points: List[DataPoint]) -> Dict[str, float]:
        """통계 정보 계산"""
        if not data_points:
            return {}

        values = [dp.value for dp in data_points]

        stats = {
            'mean': statistics.mean(values),
            'min': min(values),
            'max': max(values),
            'count': len(values)
        }

        if len(values) > 1:
            stats.update({
                'median': statistics.median(values),
                'stdev': statistics.stdev(values),
                'variance': statistics.variance(values)
            })

            # 변동계수 (CV)
            if stats['mean'] != 0:
                stats['cv'] = stats['stdev'] / abs(stats['mean'])

        return stats

    def _generate_warnings(self, data_points: List[DataPoint],
                          outliers: List[str], consensus_value: float) -> List[str]:
        """경고 메시지 생성"""
        warnings = []

        if len(data_points) < self.min_sources:
            warnings.append(f"Low source count: {len(data_points)}")

        if outliers:
            warnings.append(f"Outliers detected: {', '.join(outliers)}")

        # 높은 변동성 경고
        values = [dp.value for dp in data_points]
        if len(values) > 1:
            cv = statistics.stdev(values) / statistics.mean(values) if statistics.mean(values) != 0 else 0
            if cv > 0.1:  # 10% 이상 변동
                warnings.append(f"High volatility detected: CV={cv:.3f}")

        # 오래된 데이터 경고
        now = datetime.now()
        for dp in data_points:
            age_minutes = (now - dp.timestamp).total_seconds() / 60
            if age_minutes > 60:  # 1시간 이상 오래된 데이터
                warnings.append(f"Stale data from {dp.source}: {age_minutes:.1f} minutes old")

        return warnings

    def _update_source_reliability(self, data_points: List[DataPoint],
                                 consensus_value: float, outliers: List[str]):
        """소스 신뢰도 업데이트"""
        for dp in data_points:
            current_reliability = self.source_reliability.get(dp.source, 0.5)

            if dp.source in outliers:
                # 이상값을 제공한 소스는 신뢰도 감소
                new_reliability = current_reliability * 0.95
            else:
                # 정상적인 데이터를 제공한 소스는 신뢰도 증가
                deviation = abs((dp.value - consensus_value) / consensus_value) if consensus_value != 0 else 0
                if deviation < 0.02:  # 2% 이내 차이
                    new_reliability = min(1.0, current_reliability * 1.01)
                elif deviation < 0.05:  # 5% 이내 차이
                    new_reliability = current_reliability  # 변화 없음
                else:
                    new_reliability = current_reliability * 0.98

            self.source_reliability[dp.source] = max(0.1, min(1.0, new_reliability))

    def get_source_rankings(self) -> List[Tuple[str, float]]:
        """소스 신뢰도 순위 반환"""
        return sorted(self.source_reliability.items(), key=lambda x: x[1], reverse=True)

    def get_validation_stats(self) -> Dict[str, Any]:
        """검증 통계 반환"""
        if not self.validation_history:
            return {}

        recent_results = self.validation_history[-100:]  # 최근 100개

        quality_counts = {}
        for result in recent_results:
            quality = result.quality.value
            quality_counts[quality] = quality_counts.get(quality, 0) + 1

        avg_confidence = statistics.mean([r.confidence_score for r in recent_results])
        avg_source_count = statistics.mean([r.source_count for r in recent_results])

        return {
            'total_validations': len(self.validation_history),
            'recent_validations': len(recent_results),
            'quality_distribution': quality_counts,
            'average_confidence': round(avg_confidence, 3),
            'average_source_count': round(avg_source_count, 1),
            'source_reliability': dict(self.get_source_rankings())
        }


class MultiSourcePriceValidator:
    """다중소스 가격 검증 전용 클래스"""

    def __init__(self):
        self.validator = DataValidator()
        self._setup_default_sources()

    def _setup_default_sources(self):
        """기본 데이터 소스 설정"""
        default_sources = [
            SourceConfig("alpha_vantage", weight=1.2, trust_score=0.9),
            SourceConfig("marketstack", weight=1.0, trust_score=0.8),
            SourceConfig("coingecko", weight=1.1, trust_score=0.85),
            SourceConfig("binance", weight=0.9, trust_score=0.95),
            SourceConfig("coinbase", weight=1.0, trust_score=0.9),
            SourceConfig("kraken", weight=0.8, trust_score=0.8),
        ]

        for source in default_sources:
            self.validator.register_source(source)

    async def validate_stock_price(self, symbol: str, prices: Dict[str, float],
                                 timestamps: Optional[Dict[str, datetime]] = None) -> ValidationResult:
        """주식 가격 검증"""
        data_points = []
        now = datetime.now()

        for source, price in prices.items():
            timestamp = timestamps.get(source, now) if timestamps else now
            data_points.append(DataPoint(
                value=price,
                timestamp=timestamp,
                source=source,
                confidence=1.0
            ))

        return await self.validator.validate_price_data(symbol, data_points)

    async def validate_crypto_price(self, symbol: str, prices: Dict[str, float],
                                  timestamps: Optional[Dict[str, datetime]] = None) -> ValidationResult:
        """암호화폐 가격 검증"""
        # 암호화폐는 변동성이 크므로 임계값 조정
        original_threshold = self.validator.consensus_threshold
        self.validator.consensus_threshold = 0.10  # 10%로 확대

        try:
            result = await self.validate_stock_price(symbol, prices, timestamps)
            return result
        finally:
            self.validator.consensus_threshold = original_threshold

    def get_recommended_sources(self, asset_type: str = "stock") -> List[str]:
        """자산 유형별 추천 소스 반환"""
        rankings = self.validator.get_source_rankings()

        if asset_type == "crypto":
            crypto_sources = ["coingecko", "binance", "coinbase", "kraken"]
            return [source for source, _ in rankings if source in crypto_sources][:3]
        else:
            stock_sources = ["alpha_vantage", "marketstack"]
            return [source for source, _ in rankings if source in stock_sources][:2]


# 전역 검증기 인스턴스
_global_price_validator = None


def get_price_validator() -> MultiSourcePriceValidator:
    """전역 가격 검증기 반환"""
    global _global_price_validator
    if _global_price_validator is None:
        _global_price_validator = MultiSourcePriceValidator()
    return _global_price_validator