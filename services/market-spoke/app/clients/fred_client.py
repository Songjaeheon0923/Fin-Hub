"""
FRED (Federal Reserve Economic Data) API 클라이언트
841,000개 경제 시계열 데이터 제공 - 무료 API
"""

import asyncio
import aiohttp
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
from enum import Enum
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)


class FredUnits(Enum):
    """FRED 데이터 단위"""
    LIN = "lin"  # Levels (no transformation)
    CHG = "chg"  # Change
    CH1 = "ch1"  # Change from Year Ago
    PCH = "pch"  # Percent Change
    PC1 = "pc1"  # Percent Change from Year Ago
    PCA = "pca"  # Compounded Annual Rate of Change
    CCH = "cch"  # Continuously Compounded Rate of Change
    CCA = "cca"  # Continuously Compounded Annual Rate of Change
    LOG = "log"  # Natural Log


class FredFrequency(Enum):
    """FRED 데이터 빈도"""
    DAILY = "d"
    WEEKLY = "w"
    BIWEEKLY = "bw"
    MONTHLY = "m"
    QUARTERLY = "q"
    SEMIANNUAL = "sa"
    ANNUAL = "a"


@dataclass
class FredSeries:
    """FRED 시계열 데이터"""
    id: str
    title: str
    frequency: str
    units: str
    seasonal_adjustment: str
    last_updated: datetime
    popularity: int
    notes: str = ""


@dataclass
class FredObservation:
    """FRED 관측값"""
    date: datetime
    value: Optional[float]
    series_id: str


@dataclass
class FredCategory:
    """FRED 카테고리"""
    id: int
    name: str
    parent_id: Optional[int] = None


@dataclass
class FredEconomicIndicator:
    """경제 지표 종합 정보"""
    series_id: str
    name: str
    current_value: Optional[float]
    previous_value: Optional[float]
    change: Optional[float]
    percent_change: Optional[float]
    last_updated: datetime
    trend: str  # "up", "down", "stable"
    category: str


class FredClient:
    """FRED API 클라이언트"""

    BASE_URL = "https://api.stlouisfed.org/fred"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None

        # FRED API는 120 calls/minute 제한
        self.request_delay = 0.5

    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        if self.session:
            await self.session.close()

    async def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict:
        """HTTP API 요청"""
        if not self.session:
            self.session = aiohttp.ClientSession()

        url = f"{self.BASE_URL}{endpoint}"
        params = params or {}
        params.update({
            "api_key": self.api_key,
            "file_type": "json"
        })

        try:
            await asyncio.sleep(self.request_delay)  # Rate limiting

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"FRED API error {response.status}: {error_text}")

        except Exception as e:
            logger.error(f"FRED API request failed: {e}")
            raise

    async def get_series_info(self, series_id: str) -> Optional[FredSeries]:
        """시계열 정보 조회"""
        endpoint = "/series"
        params = {"series_id": series_id}

        try:
            response = await self._make_request(endpoint, params)
            series_data = response.get("seriess", [])

            if not series_data:
                return None

            data = series_data[0]
            return FredSeries(
                id=data["id"],
                title=data["title"],
                frequency=data["frequency"],
                units=data["units"],
                seasonal_adjustment=data.get("seasonal_adjustment", ""),
                last_updated=datetime.fromisoformat(data["last_updated"].replace("Z", "+00:00")),
                popularity=data.get("popularity", 0),
                notes=data.get("notes", "")
            )

        except Exception as e:
            logger.error(f"Error fetching series info for {series_id}: {e}")
            return None

    async def get_series_observations(self, series_id: str,
                                    start_date: str = None,
                                    end_date: str = None,
                                    limit: int = 100000,
                                    units: str = "lin",
                                    frequency: str = None) -> List[FredObservation]:
        """시계열 관측값 조회"""
        endpoint = "/series/observations"
        params = {
            "series_id": series_id,
            "limit": limit,
            "units": units
        }

        if start_date:
            params["observation_start"] = start_date
        if end_date:
            params["observation_end"] = end_date
        if frequency:
            params["frequency"] = frequency

        try:
            response = await self._make_request(endpoint, params)
            observations_data = response.get("observations", [])

            observations = []
            for obs in observations_data:
                try:
                    value = float(obs["value"]) if obs["value"] != "." else None
                except (ValueError, TypeError):
                    value = None

                observation = FredObservation(
                    date=datetime.fromisoformat(obs["date"]),
                    value=value,
                    series_id=series_id
                )
                observations.append(observation)

            return observations

        except Exception as e:
            logger.error(f"Error fetching observations for {series_id}: {e}")
            return []

    async def search_series(self, search_text: str,
                          limit: int = 1000,
                          order_by: str = "popularity") -> List[FredSeries]:
        """시계열 검색"""
        endpoint = "/series/search"
        params = {
            "search_text": search_text,
            "limit": limit,
            "order_by": order_by
        }

        try:
            response = await self._make_request(endpoint, params)
            series_data = response.get("seriess", [])

            series_list = []
            for data in series_data:
                series = FredSeries(
                    id=data["id"],
                    title=data["title"],
                    frequency=data["frequency"],
                    units=data["units"],
                    seasonal_adjustment=data.get("seasonal_adjustment", ""),
                    last_updated=datetime.fromisoformat(data["last_updated"].replace("Z", "+00:00")),
                    popularity=data.get("popularity", 0),
                    notes=data.get("notes", "")
                )
                series_list.append(series)

            return series_list

        except Exception as e:
            logger.error(f"Error searching series: {e}")
            return []

    async def get_categories(self, category_id: int = 0) -> List[FredCategory]:
        """카테고리 조회"""
        endpoint = "/category"
        params = {"category_id": category_id}

        try:
            response = await self._make_request(endpoint, params)
            categories_data = response.get("categories", [])

            categories = []
            for cat in categories_data:
                category = FredCategory(
                    id=cat["id"],
                    name=cat["name"],
                    parent_id=cat.get("parent_id")
                )
                categories.append(category)

            return categories

        except Exception as e:
            logger.error(f"Error fetching categories: {e}")
            return []

    async def get_category_series(self, category_id: int,
                                limit: int = 1000) -> List[FredSeries]:
        """카테고리별 시계열 조회"""
        endpoint = "/category/series"
        params = {
            "category_id": category_id,
            "limit": limit
        }

        try:
            response = await self._make_request(endpoint, params)
            series_data = response.get("seriess", [])

            series_list = []
            for data in series_data:
                series = FredSeries(
                    id=data["id"],
                    title=data["title"],
                    frequency=data["frequency"],
                    units=data["units"],
                    seasonal_adjustment=data.get("seasonal_adjustment", ""),
                    last_updated=datetime.fromisoformat(data["last_updated"].replace("Z", "+00:00")),
                    popularity=data.get("popularity", 0),
                    notes=data.get("notes", "")
                )
                series_list.append(series)

            return series_list

        except Exception as e:
            logger.error(f"Error fetching category series: {e}")
            return []

    async def get_multiple_series(self, series_ids: List[str],
                                start_date: str = None,
                                end_date: str = None) -> Dict[str, List[FredObservation]]:
        """다중 시계열 데이터 조회"""
        results = {}

        # 병렬로 데이터 수집
        tasks = []
        for series_id in series_ids:
            task = self.get_series_observations(series_id, start_date, end_date)
            tasks.append((series_id, task))

        # 결과 수집
        for series_id, task in tasks:
            try:
                observations = await task
                results[series_id] = observations
            except Exception as e:
                logger.error(f"Error fetching {series_id}: {e}")
                results[series_id] = []

        return results


class FredEconomicAnalyzer:
    """FRED 경제 데이터 분석기"""

    # 주요 경제 지표 시계열 ID 매핑
    KEY_INDICATORS = {
        # 금리
        "fed_funds_rate": "FEDFUNDS",
        "10y_treasury": "GS10",
        "2y_treasury": "GS2",
        "30y_mortgage": "MORTGAGE30US",

        # 인플레이션
        "cpi": "CPIAUCSL",
        "core_cpi": "CPILFESL",
        "pce": "PCEPI",
        "core_pce": "PCEPILFE",

        # 고용
        "unemployment_rate": "UNRATE",
        "nonfarm_payrolls": "PAYEMS",
        "participation_rate": "CIVPART",
        "jobless_claims": "ICSA",

        # GDP
        "real_gdp": "GDPC1",
        "gdp_growth": "A191RL1Q225SBEA",
        "gdp_deflator": "GDPDEF",

        # 소비 및 소득
        "personal_income": "PI",
        "personal_spending": "PCE",
        "retail_sales": "RSAFS",
        "consumer_sentiment": "UMCSENT",

        # 산업
        "industrial_production": "INDPRO",
        "capacity_utilization": "TCU",
        "ism_manufacturing": "NAPM",
        "ism_services": "NAPMSI",

        # 주택
        "housing_starts": "HOUST",
        "existing_home_sales": "EXHOSLUSM495S",
        "case_shiller_index": "CSUSHPISA",

        # 통화
        "money_supply_m1": "M1SL",
        "money_supply_m2": "M2SL",
        "dollar_index": "DTWEXBGS",

        # 국제
        "trade_balance": "BOPGSTB",
        "foreign_exchange_reserves": "TRESEGUSM052N"
    }

    def __init__(self, fred_client: FredClient):
        self.fred_client = fred_client
        self.indicators_cache: Dict[str, List[FredObservation]] = {}

    async def get_key_economic_indicators(self, lookback_months: int = 24) -> Dict[str, FredEconomicIndicator]:
        """주요 경제 지표 종합 조회"""
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=lookback_months * 30)).strftime("%Y-%m-%d")

        # 모든 주요 지표 데이터 수집
        series_data = await self.fred_client.get_multiple_series(
            list(self.KEY_INDICATORS.values()),
            start_date,
            end_date
        )

        indicators = {}
        for name, series_id in self.KEY_INDICATORS.items():
            observations = series_data.get(series_id, [])
            if observations:
                indicator = await self._create_economic_indicator(name, series_id, observations)
                if indicator:
                    indicators[name] = indicator

        return indicators

    async def _create_economic_indicator(self, name: str, series_id: str,
                                       observations: List[FredObservation]) -> Optional[FredEconomicIndicator]:
        """경제 지표 객체 생성"""
        if len(observations) < 2:
            return None

        # 유효한 값들만 필터링
        valid_obs = [obs for obs in observations if obs.value is not None]
        if len(valid_obs) < 2:
            return None

        # 최신 값과 이전 값
        latest = valid_obs[-1]
        previous = valid_obs[-2]

        # 변화율 계산
        change = latest.value - previous.value
        percent_change = (change / previous.value * 100) if previous.value != 0 else 0

        # 트렌드 판단
        trend = "stable"
        if abs(percent_change) > 0.1:  # 0.1% 이상 변화
            trend = "up" if percent_change > 0 else "down"

        # 카테고리 분류
        category = self._classify_indicator_category(name)

        return FredEconomicIndicator(
            series_id=series_id,
            name=name.replace("_", " ").title(),
            current_value=latest.value,
            previous_value=previous.value,
            change=change,
            percent_change=percent_change,
            last_updated=latest.date,
            trend=trend,
            category=category
        )

    def _classify_indicator_category(self, indicator_name: str) -> str:
        """지표 카테고리 분류"""
        if any(word in indicator_name for word in ["rate", "treasury", "mortgage", "funds"]):
            return "Interest Rates"
        elif any(word in indicator_name for word in ["cpi", "pce", "inflation"]):
            return "Inflation"
        elif any(word in indicator_name for word in ["unemployment", "payrolls", "jobless", "participation"]):
            return "Employment"
        elif any(word in indicator_name for word in ["gdp", "growth"]):
            return "Economic Growth"
        elif any(word in indicator_name for word in ["housing", "home"]):
            return "Housing"
        elif any(word in indicator_name for word in ["money", "dollar"]):
            return "Monetary Policy"
        else:
            return "Other"

    async def calculate_recession_probability(self) -> float:
        """경기침체 확률 계산 (Sahm Rule 기반)"""
        try:
            # 실업률 데이터 (3개월 이동평균)
            unemployment_data = await self.fred_client.get_series_observations(
                "UNRATE",
                start_date=(datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"),
                end_date=datetime.now().strftime("%Y-%m-%d")
            )

            if len(unemployment_data) < 12:
                return 0.0

            # 유효한 실업률 데이터
            valid_data = [obs.value for obs in unemployment_data if obs.value is not None]
            if len(valid_data) < 12:
                return 0.0

            df = pd.DataFrame(valid_data, columns=['unemployment_rate'])
            df['3m_avg'] = df['unemployment_rate'].rolling(window=3).mean()

            # Sahm Rule: 3개월 평균 실업률이 12개월 최저점 대비 0.5%p 이상 상승
            current_3m_avg = df['3m_avg'].iloc[-1]
            min_12m = df['3m_avg'].iloc[-12:].min()

            sahm_indicator = current_3m_avg - min_12m

            # 확률 계산 (0.5%p 기준)
            if sahm_indicator >= 0.5:
                probability = min(sahm_indicator / 0.5 * 0.8, 0.95)  # 최대 95%
            else:
                probability = max(sahm_indicator / 0.5 * 0.3, 0.0)   # 0.5%p 미만시 낮은 확률

            return probability

        except Exception as e:
            logger.error(f"Error calculating recession probability: {e}")
            return 0.0

    async def get_yield_curve_analysis(self) -> Dict[str, Any]:
        """수익률 곡선 분석"""
        try:
            # 다양한 만기 국채 수익률
            yield_series = {
                "3M": "TB3MS",
                "2Y": "GS2",
                "5Y": "GS5",
                "10Y": "GS10",
                "30Y": "GS30"
            }

            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

            yield_data = await self.fred_client.get_multiple_series(
                list(yield_series.values()),
                start_date,
                end_date
            )

            current_yields = {}
            for maturity, series_id in yield_series.items():
                observations = yield_data.get(series_id, [])
                valid_obs = [obs for obs in observations if obs.value is not None]
                if valid_obs:
                    current_yields[maturity] = valid_obs[-1].value

            # 수익률 곡선 분석
            analysis = {
                "current_yields": current_yields,
                "curve_shape": "normal",
                "inversion_signals": [],
                "steepness": 0.0
            }

            # 2Y-10Y 스프레드 (경기침체 지표)
            if "2Y" in current_yields and "10Y" in current_yields:
                spread_2y_10y = current_yields["10Y"] - current_yields["2Y"]
                analysis["2y_10y_spread"] = spread_2y_10y

                if spread_2y_10y < 0:
                    analysis["curve_shape"] = "inverted"
                    analysis["inversion_signals"].append("2Y-10Y inverted")

            # 3M-10Y 스프레드
            if "3M" in current_yields and "10Y" in current_yields:
                spread_3m_10y = current_yields["10Y"] - current_yields["3M"]
                analysis["3m_10y_spread"] = spread_3m_10y

                if spread_3m_10y < 0:
                    analysis["inversion_signals"].append("3M-10Y inverted")

            # 곡선 기울기 (30Y - 2Y)
            if "2Y" in current_yields and "30Y" in current_yields:
                analysis["steepness"] = current_yields["30Y"] - current_yields["2Y"]

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing yield curve: {e}")
            return {}

    @staticmethod
    def to_dataframe(observations: List[FredObservation]) -> pd.DataFrame:
        """관측값을 DataFrame으로 변환"""
        if not observations:
            return pd.DataFrame()

        data = []
        for obs in observations:
            if obs.value is not None:
                data.append({
                    'date': obs.date,
                    'value': obs.value
                })

        df = pd.DataFrame(data)
        if not df.empty:
            df.set_index('date', inplace=True)
            df.sort_index(inplace=True)

        return df


async def demo_fred_client():
    """FRED 클라이언트 데모"""
    # 실제 API 키 필요 (https://fred.stlouisfed.org/docs/api/api_key.html)
    API_KEY = "YOUR_FRED_API_KEY"

    async with FredClient(API_KEY) as fred:
        analyzer = FredEconomicAnalyzer(fred)

        # 1. 주요 경제 지표 조회
        print("📊 Fetching key economic indicators...")
        indicators = await analyzer.get_key_economic_indicators()

        for name, indicator in indicators.items():
            trend_icon = "📈" if indicator.trend == "up" else "📉" if indicator.trend == "down" else "➡️"
            print(f"{trend_icon} {indicator.name}: {indicator.current_value:.2f} "
                  f"({indicator.percent_change:+.2f}%)")

        # 2. 경기침체 확률
        print("\n🔍 Recession probability analysis...")
        recession_prob = await analyzer.calculate_recession_probability()
        print(f"Recession probability: {recession_prob:.1%}")

        # 3. 수익률 곡선 분석
        print("\n📈 Yield curve analysis...")
        yield_analysis = await analyzer.get_yield_curve_analysis()
        if yield_analysis:
            print(f"Curve shape: {yield_analysis['curve_shape']}")
            if yield_analysis['inversion_signals']:
                print(f"⚠️ Inversion signals: {', '.join(yield_analysis['inversion_signals'])}")

        # 4. 특정 시계열 상세 분석
        print("\n💰 Federal Funds Rate analysis...")
        fed_funds = await fred.get_series_observations("FEDFUNDS", limit=50)
        if fed_funds:
            df = FredEconomicAnalyzer.to_dataframe(fed_funds)
            print(f"Current Fed Funds Rate: {df['value'].iloc[-1]:.2f}%")
            print(f"6-month change: {df['value'].iloc[-1] - df['value'].iloc[-6]:+.2f}%")


if __name__ == "__main__":
    asyncio.run(demo_fred_client())