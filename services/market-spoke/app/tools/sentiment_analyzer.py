"""
Sentiment Analyzer Tool - Analyze market sentiment
"""
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List

from .base_tool import BaseTool


class SentimentAnalyzer(BaseTool):
    """Tool for analyzing market sentiment"""

    def __init__(self):
        super().__init__(
            tool_id="market.analyze_sentiment",
            name="Analyze Market Sentiment",
            description="시장 감성을 분석합니다"
        )

    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute sentiment analysis"""
        try:
            # Validate required arguments
            self.validate_arguments(arguments, ["keyword"])

            keyword = arguments["keyword"]
            period = arguments.get("period", "7d")  # 1d, 7d, 30d
            sources = arguments.get("sources", ["news", "social", "analyst"])
            language = arguments.get("language", "en")

            self.logger.info(f"Analyzing sentiment for '{keyword}', period: {period}")

            # Mock sentiment analysis (in real implementation, this would use NLP APIs)
            sentiment_data = await self._analyze_mock_sentiment(keyword, period, sources, language)

            return self.create_success_response(
                data=sentiment_data,
                metadata={
                    "keyword": keyword,
                    "period": period,
                    "sources": sources,
                    "language": language,
                    "model": "mock_sentiment_model",  # In real implementation: BERT, GPT, etc.
                    "timestamp": datetime.now().isoformat()
                }
            )

        except Exception as e:
            return await self.handle_error(e, "sentiment_analysis")

    async def get_tool_info(self) -> Dict[str, Any]:
        """Get tool information for MCP schema"""
        return {
            "name": self.tool_id,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "Keyword to analyze sentiment for (e.g., stock ticker, company name, market event)"
                    },
                    "period": {
                        "type": "string",
                        "description": "Time period for analysis",
                        "enum": ["1d", "7d", "30d"],
                        "default": "7d"
                    },
                    "sources": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["news", "social", "analyst", "earnings"]
                        },
                        "description": "Data sources to analyze",
                        "default": ["news", "social", "analyst"]
                    },
                    "language": {
                        "type": "string",
                        "description": "Language for analysis",
                        "enum": ["en", "ko", "zh", "ja"],
                        "default": "en"
                    }
                },
                "required": ["keyword"]
            }
        }

    async def _analyze_mock_sentiment(self, keyword: str, period: str, sources: List[str], language: str) -> Dict[str, Any]:
        """Generate mock sentiment analysis"""
        # Generate overall sentiment scores
        positive_weight = random.uniform(0.2, 0.6)
        negative_weight = random.uniform(0.1, 0.4)
        neutral_weight = 1.0 - positive_weight - negative_weight

        if neutral_weight < 0:
            neutral_weight = 0.1
            total = positive_weight + negative_weight + neutral_weight
            positive_weight /= total
            negative_weight /= total
            neutral_weight /= total

        overall_sentiment = {
            "score": round(positive_weight - negative_weight, 3),  # Range: -1 to 1
            "confidence": round(random.uniform(0.7, 0.95), 3),
            "distribution": {
                "positive": round(positive_weight * 100, 1),
                "negative": round(negative_weight * 100, 1),
                "neutral": round(neutral_weight * 100, 1)
            },
            "trend": random.choice(["bullish", "bearish", "neutral", "mixed"])
        }

        # Generate source-specific sentiment
        source_sentiment = {}
        for source in sources:
            source_sentiment[source] = await self._generate_source_sentiment(source)

        # Generate historical sentiment data
        historical_sentiment = await self._generate_historical_sentiment(period)

        # Generate key insights
        insights = await self._generate_sentiment_insights(keyword, overall_sentiment, source_sentiment)

        # Generate top keywords/topics
        keywords = await self._generate_top_keywords(keyword, sources)

        return {
            "keyword": keyword,
            "overall_sentiment": overall_sentiment,
            "source_breakdown": source_sentiment,
            "historical_data": historical_sentiment,
            "insights": insights,
            "top_keywords": keywords,
            "period": period,
            "sources_analyzed": sources,
            "language": language,
            "last_updated": datetime.now().isoformat()
        }

    async def _generate_source_sentiment(self, source: str) -> Dict[str, Any]:
        """Generate sentiment data for a specific source"""
        # Different sources might have different sentiment patterns
        source_patterns = {
            "news": {"bias": 0.1, "volatility": 0.3},
            "social": {"bias": -0.05, "volatility": 0.5},
            "analyst": {"bias": 0.15, "volatility": 0.2},
            "earnings": {"bias": 0.05, "volatility": 0.4}
        }

        pattern = source_patterns.get(source, {"bias": 0, "volatility": 0.3})

        score = pattern["bias"] + random.uniform(-pattern["volatility"], pattern["volatility"])
        score = max(-1, min(1, score))  # Clamp to [-1, 1]

        positive = max(0.1, 0.5 + score * 0.4)
        negative = max(0.1, 0.5 - score * 0.4)
        neutral = 1.0 - positive - negative

        if neutral < 0:
            neutral = 0.1
            total = positive + negative + neutral
            positive /= total
            negative /= total
            neutral /= total

        return {
            "score": round(score, 3),
            "confidence": round(random.uniform(0.6, 0.9), 3),
            "distribution": {
                "positive": round(positive * 100, 1),
                "negative": round(negative * 100, 1),
                "neutral": round(neutral * 100, 1)
            },
            "volume": random.randint(50, 1000),
            "sources_count": random.randint(5, 50)
        }

    async def _generate_historical_sentiment(self, period: str) -> List[Dict[str, Any]]:
        """Generate historical sentiment data"""
        period_days = {
            "1d": 1,
            "7d": 7,
            "30d": 30
        }

        days = period_days.get(period, 7)
        data_points = min(days, 30)

        historical = []
        base_score = random.uniform(-0.3, 0.3)

        for i in range(data_points):
            date = datetime.now() - timedelta(days=data_points - i - 1)

            # Random walk for sentiment
            score_change = random.uniform(-0.1, 0.1)
            base_score = max(-1, min(1, base_score + score_change))

            historical.append({
                "date": date.strftime("%Y-%m-%d"),
                "score": round(base_score, 3),
                "volume": random.randint(100, 2000),
                "confidence": round(random.uniform(0.6, 0.9), 3)
            })

        return historical

    async def _generate_sentiment_insights(self, keyword: str, overall: Dict, sources: Dict) -> List[str]:
        """Generate key insights from sentiment analysis"""
        insights = []

        # Overall sentiment insights
        if overall["score"] > 0.2:
            insights.append(f"Strong positive sentiment detected for {keyword}")
        elif overall["score"] < -0.2:
            insights.append(f"Notable negative sentiment observed for {keyword}")
        else:
            insights.append(f"Mixed or neutral sentiment prevails for {keyword}")

        # Confidence insights
        if overall["confidence"] > 0.85:
            insights.append("High confidence in sentiment analysis results")
        elif overall["confidence"] < 0.7:
            insights.append("Lower confidence due to mixed or unclear signals")

        # Source comparison insights
        if "news" in sources and "social" in sources:
            news_score = sources["news"]["score"]
            social_score = sources["social"]["score"]

            if abs(news_score - social_score) > 0.3:
                if news_score > social_score:
                    insights.append("News sentiment more positive than social media sentiment")
                else:
                    insights.append("Social media sentiment more positive than news sentiment")

        # Trend insights
        trend = overall.get("trend", "neutral")
        if trend == "bullish":
            insights.append("Bullish sentiment trend indicates potential upward price pressure")
        elif trend == "bearish":
            insights.append("Bearish sentiment trend suggests possible downward price pressure")

        # Add some randomized contextual insights
        context_insights = [
            f"Recent sentiment volatility suggests market uncertainty around {keyword}",
            f"Sentiment analysis indicates {keyword} is receiving increased attention",
            f"Current sentiment levels are within normal range for {keyword}",
            f"Sentiment momentum building around {keyword}",
            f"Mixed signals in sentiment data require careful interpretation"
        ]
        insights.extend(random.sample(context_insights, min(2, len(context_insights))))

        return insights[:5]  # Return top 5 insights

    async def _generate_top_keywords(self, main_keyword: str, sources: List[str]) -> Dict[str, Any]:
        """Generate top keywords and topics"""
        # Mock keyword extraction (in real implementation, this would use NLP)
        positive_keywords = [
            "growth", "bullish", "opportunity", "strong", "positive",
            "upward", "momentum", "buy", "promising", "optimistic"
        ]

        negative_keywords = [
            "decline", "bearish", "risk", "weak", "negative",
            "downward", "sell", "concerning", "pessimistic", "uncertain"
        ]

        neutral_keywords = [
            "earnings", "report", "analysis", "forecast", "outlook",
            "market", "trading", "volume", "price", "activity"
        ]

        # Randomly select keywords with some weighting
        selected_positive = random.sample(positive_keywords, random.randint(2, 4))
        selected_negative = random.sample(negative_keywords, random.randint(1, 3))
        selected_neutral = random.sample(neutral_keywords, random.randint(3, 5))

        # Generate keyword data with mock frequencies
        keywords_data = []

        for keyword in selected_positive:
            keywords_data.append({
                "keyword": keyword,
                "frequency": random.randint(50, 200),
                "sentiment": "positive",
                "relevance": round(random.uniform(0.6, 0.9), 2)
            })

        for keyword in selected_negative:
            keywords_data.append({
                "keyword": keyword,
                "frequency": random.randint(30, 150),
                "sentiment": "negative",
                "relevance": round(random.uniform(0.5, 0.8), 2)
            })

        for keyword in selected_neutral:
            keywords_data.append({
                "keyword": keyword,
                "frequency": random.randint(40, 300),
                "sentiment": "neutral",
                "relevance": round(random.uniform(0.7, 0.95), 2)
            })

        # Sort by frequency
        keywords_data.sort(key=lambda x: x["frequency"], reverse=True)

        # Generate topic clusters
        topics = [
            {"topic": "Financial Performance", "weight": random.uniform(0.2, 0.4)},
            {"topic": "Market Outlook", "weight": random.uniform(0.15, 0.35)},
            {"topic": "Company News", "weight": random.uniform(0.1, 0.3)},
            {"topic": "Industry Trends", "weight": random.uniform(0.05, 0.25)},
            {"topic": "Economic Factors", "weight": random.uniform(0.05, 0.2)}
        ]

        return {
            "keywords": keywords_data[:15],  # Top 15 keywords
            "topics": topics,
            "entities": [
                {"entity": main_keyword, "type": "stock", "mentions": random.randint(100, 500)},
                {"entity": f"{main_keyword} Corp", "type": "company", "mentions": random.randint(50, 200)},
                {"entity": "Market", "type": "concept", "mentions": random.randint(200, 800)}
            ]
        }