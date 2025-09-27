"""
Fin-Hub Technical Indicators Library
Jesse AI 스타일 300+ 기술지표 사전 계산 시스템
"""

from .base import BaseIndicator
from .trend import *
from .momentum import *
from .volatility import *
from .volume import *
from .support_resistance import *
from .alpha158 import *

__version__ = "1.0.0"

# 모든 지표 레지스트리
INDICATOR_REGISTRY = {}

def register_indicator(name: str):
    """지표 등록 데코레이터"""
    def decorator(cls):
        INDICATOR_REGISTRY[name] = cls
        return cls
    return decorator

def get_indicator(name: str):
    """지표 인스턴스 반환"""
    if name in INDICATOR_REGISTRY:
        return INDICATOR_REGISTRY[name]()
    raise ValueError(f"Unknown indicator: {name}")

def list_indicators():
    """사용 가능한 모든 지표 목록 반환"""
    return list(INDICATOR_REGISTRY.keys())