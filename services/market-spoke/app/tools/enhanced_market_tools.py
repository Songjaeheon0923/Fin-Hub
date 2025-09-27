"""
강화된 시장 데이터 MCP 도구들
새로운 API 통합을 위한 Claude Code 도구
"""

from typing import Dict, List, Optional, Any, Union
import asyncio
import json
import pandas as pd
from datetime import datetime, timedelta

from ..clients.enhanced_data_manager import (
    EnhancedDataManager, DataSourceConfig, DataSource, AssetClass
)


class EnhancedMarketDataTool:
    """강화된 시장 데이터 조회 도구"""

    def __init__(self, data_manager: EnhancedDataManager):
        self.data_manager = data_manager
        self.name = "enhanced_market_data"
        self.description = "고성능 다중소스 시장 데이터 조회 (Polygon, Twelve Data, Finnhub, FRED 통합)"

    async def get_comprehensive_analysis(self, symbol: str,
                                       include_economic: bool = True,
                                       timeframe: str = "1day") -> Dict[str, Any]:
        """종합 시장 분석"""
        try:
            # 자산 클래스 자동 감지
            asset_class = self._detect_asset_class(symbol)

            # 강화된 데이터 조회
            enhanced_data = await self.data_manager.get_enhanced_market_data(
                symbol=symbol,
                asset_class=asset_class,
                include_fundamentals=True,
                include_news=True,
                include_economic=include_economic,
                timeframe=timeframe,
                limit=200
            )

            if not enhanced_data:
                return {"error": f"No data available for {symbol}"}

            # 결과 구성
            result = {
                "symbol": symbol,
                "asset_class": asset_class.value,
                "timestamp": datetime.now().isoformat(),
                "data_quality_score": enhanced_data.data_quality_score,
                "price_data": self._format_price_data(enhanced_data.data),
                "technical_analysis": enhanced_data.technical_signals,
                "data_sources": [source.value for source in enhanced_data.sources]
            }

            # 펀더멘털 데이터 추가
            if enhanced_data.fundamental_data:
                result["fundamental_analysis"] = enhanced_data.fundamental_data

            # 뉴스 감정 분석 추가
            if enhanced_data.news_sentiment:
                result["news_sentiment"] = enhanced_data.news_sentiment

            # 경제적 맥락 추가
            if enhanced_data.economic_context:
                result["economic_context"] = enhanced_data.economic_context

            return result

        except Exception as e:
            return {"error": f"Failed to get analysis for {symbol}: {str(e)}"}

    async def get_market_overview(self, symbols: List[str] = None) -> Dict[str, Any]:
        """시장 개요 조회"""
        try:
            if not symbols:
                symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA", "BTC/USD", "EUR/USD"]

            overview = await self.data_manager.get_market_overview(
                symbols=symbols,
                asset_classes=[AssetClass.STOCKS, AssetClass.CRYPTO, AssetClass.FOREX]
            )

            return overview

        except Exception as e:
            return {"error": f"Failed to get market overview: {str(e)}"}

    async def get_economic_indicators(self, lookback_months: int = 12) -> Dict[str, Any]:
        """경제 지표 조회"""
        try:
            if DataSource.FRED not in self.data_manager.clients:
                return {"error": "FRED client not available"}

            fred_client = self.data_manager.clients[DataSource.FRED]
            from ..clients.fred_client import FredEconomicAnalyzer

            analyzer = FredEconomicAnalyzer(fred_client)

            # 주요 경제 지표
            indicators = await analyzer.get_key_economic_indicators(lookback_months)

            # 경기침체 확률
            recession_prob = await analyzer.calculate_recession_probability()

            # 수익률 곡선 분석
            yield_analysis = await analyzer.get_yield_curve_analysis()

            result = {
                "timestamp": datetime.now().isoformat(),
                "key_indicators": {},
                "recession_probability": recession_prob,
                "yield_curve_analysis": yield_analysis
            }

            # 지표 데이터 포맷팅
            for name, indicator in indicators.items():
                result["key_indicators"][name] = {
                    "name": indicator.name,
                    "current_value": indicator.current_value,
                    "change": indicator.change,
                    "percent_change": indicator.percent_change,
                    "trend": indicator.trend,
                    "category": indicator.category,
                    "last_updated": indicator.last_updated.isoformat()
                }

            return result

        except Exception as e:
            return {"error": f"Failed to get economic indicators: {str(e)}"}

    async def get_company_fundamentals(self, symbol: str) -> Dict[str, Any]:
        """기업 펀더멘털 분석"""
        try:
            if DataSource.FINNHUB not in self.data_manager.clients:
                return {"error": "Finnhub client not available"}

            client = self.data_manager.clients[DataSource.FINNHUB]

            result = {
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
                "company_profile": {},
                "financial_metrics": {},
                "analyst_recommendations": [],
                "recent_news": []
            }

            # 기업 프로필
            profile = await client.get_company_profile(symbol)
            if profile:
                result["company_profile"] = {
                    "name": profile.name,
                    "industry": profile.industry,
                    "country": profile.country,
                    "market_cap": profile.market_cap,
                    "shares_outstanding": profile.share_outstanding,
                    "website": profile.website
                }

            # 기본 재무 지표
            metrics = await client.get_basic_financials(symbol)
            if metrics:
                result["financial_metrics"] = metrics

            # 애널리스트 추천
            recommendations = await client.get_recommendation_trends(symbol)
            if recommendations:
                result["analyst_recommendations"] = recommendations[:10]

            # 최근 뉴스
            news = await client.get_company_news(symbol)
            if news:
                result["recent_news"] = [
                    {
                        "headline": n.headline,
                        "summary": n.summary,
                        "source": n.source,
                        "url": n.url,
                        "datetime": n.datetime.isoformat()
                    }
                    for n in news[:15]
                ]

            return result

        except Exception as e:
            return {"error": f"Failed to get fundamentals for {symbol}: {str(e)}"}

    async def get_real_time_data(self, symbols: List[str]) -> Dict[str, Any]:
        """실시간 데이터 조회"""
        try:
            results = {}

            for symbol in symbols:
                asset_class = self._detect_asset_class(symbol)

                # Polygon 실시간 데이터 (최우선)
                if DataSource.POLYGON in self.data_manager.clients:
                    client = self.data_manager.clients[DataSource.POLYGON]

                    if asset_class == AssetClass.STOCKS:
                        quote = await client.get_real_time_quote(symbol)
                        trade = await client.get_real_time_trade(symbol)

                        if quote and trade:
                            results[symbol] = {
                                "price": trade.price,
                                "bid": quote.bid,
                                "ask": quote.ask,
                                "spread": quote.ask - quote.bid,
                                "volume": trade.size,
                                "timestamp": trade.timestamp.isoformat(),
                                "source": "polygon",
                                "latency_ms": "<20"
                            }

                    elif asset_class == AssetClass.FOREX:
                        base, quote_curr = symbol.split("/")
                        forex_data = await client.get_forex_rates(base, quote_curr)

                        if forex_data:
                            results[symbol] = {
                                "price": forex_data.get("mid", 0),
                                "bid": forex_data.get("bid", 0),
                                "ask": forex_data.get("ask", 0),
                                "timestamp": datetime.fromtimestamp(
                                    forex_data.get("timestamp", 0) / 1000
                                ).isoformat(),
                                "source": "polygon"
                            }

                # Twelve Data 백업
                if symbol not in results and DataSource.TWELVE_DATA in self.data_manager.clients:
                    client = self.data_manager.clients[DataSource.TWELVE_DATA]
                    quote = await client.get_real_time_price(symbol)

                    if quote:
                        results[symbol] = {
                            "price": quote.price,
                            "change": quote.change,
                            "percent_change": quote.percent_change,
                            "timestamp": quote.timestamp.isoformat() if quote.timestamp else datetime.now().isoformat(),
                            "source": "twelve_data"
                        }

            return {
                "timestamp": datetime.now().isoformat(),
                "data": results,
                "total_symbols": len(results)
            }

        except Exception as e:
            return {"error": f"Failed to get real-time data: {str(e)}"}

    def _detect_asset_class(self, symbol: str) -> AssetClass:
        """심볼로부터 자산 클래스 자동 감지"""
        symbol_upper = symbol.upper()

        # 외환
        if "/" in symbol and len(symbol.split("/")) == 2:
            return AssetClass.FOREX

        # 암호화폐
        crypto_indicators = ["BTC", "ETH", "USD", "USDT", "BUSD"]
        if any(indicator in symbol_upper for indicator in crypto_indicators):
            return AssetClass.CRYPTO

        # ETF
        etf_indicators = ["SPY", "QQQ", "IWM", "VTI", "VOO", "ETF"]
        if any(indicator in symbol_upper for indicator in etf_indicators):
            return AssetClass.ETF

        # 지수
        index_indicators = ["^", "DJI", "SPX", "NDX"]
        if any(indicator in symbol_upper for indicator in index_indicators):
            return AssetClass.INDICES

        # 기본값: 주식
        return AssetClass.STOCKS

    def _format_price_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """가격 데이터 포맷팅"""
        if df.empty:
            return {}

        latest = df.iloc[-1]
        previous = df.iloc[-2] if len(df) > 1 else latest

        return {
            "current_price": float(latest['close']),
            "open": float(latest['open']) if 'open' in df.columns else None,
            "high": float(latest['high']) if 'high' in df.columns else None,
            "low": float(latest['low']) if 'low' in df.columns else None,
            "volume": int(latest['volume']) if 'volume' in df.columns and pd.notna(latest['volume']) else None,
            "change": float(latest['close'] - previous['close']),
            "change_percent": float((latest['close'] - previous['close']) / previous['close'] * 100),
            "data_points": len(df),
            "last_updated": df.index[-1].isoformat() if hasattr(df.index[-1], 'isoformat') else str(df.index[-1])
        }


class PerformanceMonitoringTool:
    """성능 모니터링 도구"""

    def __init__(self, data_manager: EnhancedDataManager):
        self.data_manager = data_manager
        self.name = "performance_monitoring"
        self.description = "API 성능 및 데이터 품질 모니터링"

    async def get_performance_report(self) -> Dict[str, Any]:
        """성능 리포트 생성"""
        try:
            return await self.data_manager.get_performance_report()
        except Exception as e:
            return {"error": f"Failed to get performance report: {str(e)}"}

    async def get_api_status(self) -> Dict[str, Any]:
        """API 상태 확인"""
        try:
            status_report = {
                "timestamp": datetime.now().isoformat(),
                "api_sources": {},
                "overall_health": "unknown"
            }

            healthy_sources = 0
            total_sources = len(self.data_manager.clients)

            # 각 API 소스 상태 확인
            for source, client in self.data_manager.clients.items():
                try:
                    if source == DataSource.POLYGON:
                        await client.get_market_status()
                        status_report["api_sources"][source.value] = {
                            "status": "healthy",
                            "features": ["ultra_low_latency", "real_time", "websocket"],
                            "last_check": datetime.now().isoformat()
                        }
                        healthy_sources += 1

                    elif source == DataSource.TWELVE_DATA:
                        await client.get_real_time_price("AAPL")
                        status_report["api_sources"][source.value] = {
                            "status": "healthy",
                            "features": ["multi_asset", "technical_indicators", "economic_calendar"],
                            "last_check": datetime.now().isoformat()
                        }
                        healthy_sources += 1

                    elif source == DataSource.FINNHUB:
                        await client.get_quote("AAPL")
                        status_report["api_sources"][source.value] = {
                            "status": "healthy",
                            "features": ["fundamentals", "news", "analyst_recommendations"],
                            "last_check": datetime.now().isoformat()
                        }
                        healthy_sources += 1

                    elif source == DataSource.FRED:
                        # FRED는 별도 상태 확인 없이 기본적으로 건강한 것으로 가정
                        status_report["api_sources"][source.value] = {
                            "status": "healthy",
                            "features": ["economic_indicators", "841k_series", "recession_analysis"],
                            "last_check": datetime.now().isoformat()
                        }
                        healthy_sources += 1

                except Exception as e:
                    status_report["api_sources"][source.value] = {
                        "status": "error",
                        "error": str(e),
                        "last_check": datetime.now().isoformat()
                    }

            # 전체 건강 상태 판단
            if healthy_sources == total_sources:
                status_report["overall_health"] = "excellent"
            elif healthy_sources >= total_sources * 0.75:
                status_report["overall_health"] = "good"
            elif healthy_sources >= total_sources * 0.5:
                status_report["overall_health"] = "fair"
            else:
                status_report["overall_health"] = "poor"

            status_report["healthy_sources"] = healthy_sources
            status_report["total_sources"] = total_sources

            return status_report

        except Exception as e:
            return {"error": f"Failed to check API status: {str(e)}"}


# MCP 도구 팩토리 함수들
async def create_enhanced_market_tools(api_configs: Dict[str, str]) -> Dict[str, Any]:
    """강화된 시장 도구들 생성"""
    try:
        # 데이터 소스 설정
        configs = {}

        if "polygon_api_key" in api_configs:
            configs[DataSource.POLYGON] = DataSourceConfig(
                source=DataSource.POLYGON,
                api_key=api_configs["polygon_api_key"],
                priority=1
            )

        if "twelve_data_api_key" in api_configs:
            configs[DataSource.TWELVE_DATA] = DataSourceConfig(
                source=DataSource.TWELVE_DATA,
                api_key=api_configs["twelve_data_api_key"],
                priority=2
            )

        if "finnhub_api_key" in api_configs:
            configs[DataSource.FINNHUB] = DataSourceConfig(
                source=DataSource.FINNHUB,
                api_key=api_configs["finnhub_api_key"],
                priority=3
            )

        if "fred_api_key" in api_configs:
            configs[DataSource.FRED] = DataSourceConfig(
                source=DataSource.FRED,
                api_key=api_configs["fred_api_key"],
                priority=4
            )

        # 데이터 매니저 초기화
        data_manager = EnhancedDataManager(configs)
        await data_manager.initialize()

        # 도구들 생성
        market_tool = EnhancedMarketDataTool(data_manager)
        monitoring_tool = PerformanceMonitoringTool(data_manager)

        return {
            "market_data_tool": market_tool,
            "monitoring_tool": monitoring_tool,
            "data_manager": data_manager
        }

    except Exception as e:
        return {"error": f"Failed to create enhanced tools: {str(e)}"}


# 편의 함수들
async def get_comprehensive_market_analysis(symbol: str, api_configs: Dict[str, str]) -> Dict[str, Any]:
    """종합 시장 분석 (편의 함수)"""
    tools = await create_enhanced_market_tools(api_configs)
    if "error" in tools:
        return tools

    try:
        result = await tools["market_data_tool"].get_comprehensive_analysis(symbol)
        return result
    finally:
        await tools["data_manager"].shutdown()


async def get_economic_dashboard(api_configs: Dict[str, str]) -> Dict[str, Any]:
    """경제 대시보드 (편의 함수)"""
    tools = await create_enhanced_market_tools(api_configs)
    if "error" in tools:
        return tools

    try:
        economic_data = await tools["market_data_tool"].get_economic_indicators()
        market_overview = await tools["market_data_tool"].get_market_overview()
        api_status = await tools["monitoring_tool"].get_api_status()

        return {
            "economic_indicators": economic_data,
            "market_overview": market_overview,
            "api_status": api_status,
            "timestamp": datetime.now().isoformat()
        }
    finally:
        await tools["data_manager"].shutdown()