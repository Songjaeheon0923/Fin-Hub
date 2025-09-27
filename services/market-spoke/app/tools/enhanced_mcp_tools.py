"""
강화된 MCP 도구 정의
Phase 1 API 통합을 위한 Claude Code 도구들
"""

import os
from typing import Dict, Any, List, Optional
import asyncio
import json

from ..tools.enhanced_market_tools import (
    create_enhanced_market_tools,
    get_comprehensive_market_analysis,
    get_economic_dashboard
)


# API 키 설정 (환경변수에서 로드)
API_CONFIGS = {
    "polygon_api_key": os.getenv("POLYGON_API_KEY", ""),
    "twelve_data_api_key": os.getenv("TWELVE_DATA_API_KEY", ""),
    "finnhub_api_key": os.getenv("FINNHUB_API_KEY", ""),
    "fred_api_key": os.getenv("FRED_API_KEY", "")
}


async def enhanced_market_analysis(symbol: str,
                                 include_economic: bool = True,
                                 timeframe: str = "1day") -> Dict[str, Any]:
    """
    종합 시장 분석 도구

    Args:
        symbol: 분석할 심볼 (예: AAPL, BTC/USD, EUR/USD)
        include_economic: 경제 지표 포함 여부
        timeframe: 시간 프레임 (1day, 1h, 5m 등)

    Returns:
        종합 시장 분석 결과
    """
    try:
        result = await get_comprehensive_market_analysis(symbol, API_CONFIGS)
        return result
    except Exception as e:
        return {"error": f"Analysis failed for {symbol}: {str(e)}"}


async def real_time_market_data(symbols: List[str]) -> Dict[str, Any]:
    """
    실시간 시장 데이터 조회

    Args:
        symbols: 조회할 심볼 리스트

    Returns:
        실시간 시장 데이터
    """
    try:
        tools = await create_enhanced_market_tools(API_CONFIGS)
        if "error" in tools:
            return tools

        result = await tools["market_data_tool"].get_real_time_data(symbols)
        await tools["data_manager"].shutdown()
        return result
    except Exception as e:
        return {"error": f"Real-time data fetch failed: {str(e)}"}


async def economic_indicators_analysis(lookback_months: int = 12) -> Dict[str, Any]:
    """
    경제 지표 분석

    Args:
        lookback_months: 분석 기간 (개월)

    Returns:
        경제 지표 분석 결과
    """
    try:
        tools = await create_enhanced_market_tools(API_CONFIGS)
        if "error" in tools:
            return tools

        result = await tools["market_data_tool"].get_economic_indicators(lookback_months)
        await tools["data_manager"].shutdown()
        return result
    except Exception as e:
        return {"error": f"Economic analysis failed: {str(e)}"}


async def company_fundamentals_analysis(symbol: str) -> Dict[str, Any]:
    """
    기업 펀더멘털 분석

    Args:
        symbol: 기업 심볼 (예: AAPL)

    Returns:
        펀더멘털 분석 결과
    """
    try:
        tools = await create_enhanced_market_tools(API_CONFIGS)
        if "error" in tools:
            return tools

        result = await tools["market_data_tool"].get_company_fundamentals(symbol)
        await tools["data_manager"].shutdown()
        return result
    except Exception as e:
        return {"error": f"Fundamental analysis failed for {symbol}: {str(e)}"}


async def market_overview_dashboard(symbols: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    시장 개요 대시보드

    Args:
        symbols: 포함할 심볼들 (기본값: 주요 주식, 암호화폐, 외환)

    Returns:
        시장 개요 데이터
    """
    try:
        if not symbols:
            symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA", "BTC/USD", "EUR/USD", "GLD", "SPY"]

        tools = await create_enhanced_market_tools(API_CONFIGS)
        if "error" in tools:
            return tools

        result = await tools["market_data_tool"].get_market_overview(symbols)
        await tools["data_manager"].shutdown()
        return result
    except Exception as e:
        return {"error": f"Market overview failed: {str(e)}"}


async def enhanced_economic_dashboard() -> Dict[str, Any]:
    """
    강화된 경제 대시보드

    Returns:
        경제 지표, 시장 개요, API 상태를 포함한 종합 대시보드
    """
    try:
        result = await get_economic_dashboard(API_CONFIGS)
        return result
    except Exception as e:
        return {"error": f"Economic dashboard failed: {str(e)}"}


async def api_performance_monitoring() -> Dict[str, Any]:
    """
    API 성능 모니터링

    Returns:
        API 상태 및 성능 지표
    """
    try:
        tools = await create_enhanced_market_tools(API_CONFIGS)
        if "error" in tools:
            return tools

        performance_report = await tools["monitoring_tool"].get_performance_report()
        api_status = await tools["monitoring_tool"].get_api_status()

        result = {
            "performance_report": performance_report,
            "api_status": api_status,
            "timestamp": performance_report.get("timestamp")
        }

        await tools["data_manager"].shutdown()
        return result
    except Exception as e:
        return {"error": f"Performance monitoring failed: {str(e)}"}


async def multi_asset_portfolio_analysis(portfolio: Dict[str, float]) -> Dict[str, Any]:
    """
    다중 자산 포트폴리오 분석

    Args:
        portfolio: 심볼과 비중의 딕셔너리 (예: {"AAPL": 0.3, "GOOGL": 0.2, "BTC/USD": 0.1})

    Returns:
        포트폴리오 분석 결과
    """
    try:
        tools = await create_enhanced_market_tools(API_CONFIGS)
        if "error" in tools:
            return tools

        # 각 자산의 데이터 수집
        portfolio_data = {}
        total_weight = sum(portfolio.values())

        for symbol, weight in portfolio.items():
            if weight > 0:
                asset_data = await tools["market_data_tool"].get_comprehensive_analysis(symbol)
                if "error" not in asset_data:
                    portfolio_data[symbol] = {
                        "data": asset_data,
                        "weight": weight / total_weight,  # 정규화된 비중
                        "weighted_return": 0.0
                    }

        # 포트폴리오 성과 계산
        portfolio_return = 0.0
        portfolio_risk = 0.0

        for symbol, data in portfolio_data.items():
            if "price_data" in data["data"]:
                daily_return = data["data"]["price_data"].get("change_percent", 0)
                weighted_return = daily_return * data["weight"]
                portfolio_return += weighted_return
                data["weighted_return"] = weighted_return

        result = {
            "portfolio_summary": {
                "total_return": portfolio_return,
                "total_assets": len(portfolio_data),
                "timestamp": tools["market_data_tool"]._format_price_data({})
            },
            "asset_breakdown": portfolio_data,
            "recommendations": []
        }

        # 포트폴리오 권고사항
        if portfolio_return < -2.0:
            result["recommendations"].append("포트폴리오가 큰 하락세입니다. 리스크 관리를 검토하세요.")
        elif portfolio_return > 3.0:
            result["recommendations"].append("포트폴리오가 강한 상승세입니다. 이익 실현을 고려하세요.")

        if len(portfolio_data) < 5:
            result["recommendations"].append("포트폴리오 다양화를 위해 더 많은 자산 클래스를 고려하세요.")

        await tools["data_manager"].shutdown()
        return result
    except Exception as e:
        return {"error": f"Portfolio analysis failed: {str(e)}"}


# MCP 도구 스키마 정의
MCP_TOOL_SCHEMAS = {
    "enhanced_market_analysis": {
        "name": "enhanced_market_analysis",
        "description": "종합 시장 분석 (Polygon, Twelve Data, Finnhub, FRED 통합)",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "분석할 심볼 (예: AAPL, BTC/USD, EUR/USD)"
                },
                "include_economic": {
                    "type": "boolean",
                    "description": "경제 지표 포함 여부",
                    "default": True
                },
                "timeframe": {
                    "type": "string",
                    "description": "시간 프레임 (1day, 1h, 5m 등)",
                    "default": "1day"
                }
            },
            "required": ["symbol"]
        }
    },

    "real_time_market_data": {
        "name": "real_time_market_data",
        "description": "실시간 시장 데이터 조회 (<20ms 지연시간)",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbols": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "조회할 심볼 리스트"
                }
            },
            "required": ["symbols"]
        }
    },

    "economic_indicators_analysis": {
        "name": "economic_indicators_analysis",
        "description": "FRED 841,000개 경제 시계열 데이터 분석",
        "input_schema": {
            "type": "object",
            "properties": {
                "lookback_months": {
                    "type": "integer",
                    "description": "분석 기간 (개월)",
                    "default": 12,
                    "minimum": 1,
                    "maximum": 60
                }
            }
        }
    },

    "company_fundamentals_analysis": {
        "name": "company_fundamentals_analysis",
        "description": "기업 펀더멘털 분석 (재무제표, 뉴스, 애널리스트 의견)",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "기업 심볼 (예: AAPL)"
                }
            },
            "required": ["symbol"]
        }
    },

    "market_overview_dashboard": {
        "name": "market_overview_dashboard",
        "description": "시장 개요 대시보드",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbols": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "포함할 심볼들 (기본값: 주요 지수, 주식, 암호화폐, 외환)"
                }
            }
        }
    },

    "enhanced_economic_dashboard": {
        "name": "enhanced_economic_dashboard",
        "description": "강화된 경제 대시보드 (경제지표 + 시장개요 + API상태)",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },

    "api_performance_monitoring": {
        "name": "api_performance_monitoring",
        "description": "API 성능 및 상태 모니터링",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },

    "multi_asset_portfolio_analysis": {
        "name": "multi_asset_portfolio_analysis",
        "description": "다중 자산 포트폴리오 분석",
        "input_schema": {
            "type": "object",
            "properties": {
                "portfolio": {
                    "type": "object",
                    "description": "심볼과 비중의 딕셔너리",
                    "additionalProperties": {"type": "number"}
                }
            },
            "required": ["portfolio"]
        }
    }
}


# 도구 함수 매핑
TOOL_FUNCTIONS = {
    "enhanced_market_analysis": enhanced_market_analysis,
    "real_time_market_data": real_time_market_data,
    "economic_indicators_analysis": economic_indicators_analysis,
    "company_fundamentals_analysis": company_fundamentals_analysis,
    "market_overview_dashboard": market_overview_dashboard,
    "enhanced_economic_dashboard": enhanced_economic_dashboard,
    "api_performance_monitoring": api_performance_monitoring,
    "multi_asset_portfolio_analysis": multi_asset_portfolio_analysis,
}


async def get_enhanced_tools_registry() -> List[Dict[str, Any]]:
    """강화된 도구들의 레지스트리 정보 반환"""
    return [
        {
            "tool_id": tool_name,
            "tool_type": "analysis",
            "spoke_id": "market-spoke",
            "name": schema["name"],
            "description": schema["description"],
            "input_schema": schema["input_schema"],
            "version": "1.0.0",
            "enabled": True,
            "tags": ["enhanced", "multi-source", "real-time"],
            "function": TOOL_FUNCTIONS[tool_name]
        }
        for tool_name, schema in MCP_TOOL_SCHEMAS.items()
    ]


if __name__ == "__main__":
    # 테스트용
    async def test_enhanced_tools():
        """강화된 도구들 테스트"""
        print("🔧 Testing Enhanced Market Tools...")

        # 1. 종합 시장 분석
        print("\n📊 Testing comprehensive market analysis...")
        result = await enhanced_market_analysis("AAPL")
        print(f"AAPL Analysis: {json.dumps(result, indent=2)[:200]}...")

        # 2. 실시간 데이터
        print("\n⚡ Testing real-time data...")
        result = await real_time_market_data(["AAPL", "GOOGL"])
        print(f"Real-time data: {json.dumps(result, indent=2)[:200]}...")

        # 3. 경제 지표
        print("\n📈 Testing economic indicators...")
        result = await economic_indicators_analysis(6)
        print(f"Economic indicators: {json.dumps(result, indent=2)[:200]}...")

    asyncio.run(test_enhanced_tools())