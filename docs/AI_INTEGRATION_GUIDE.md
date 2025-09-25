# AI Integration Guide for Fin-Hub APIs

## Quick Reference for AI Agents

### 1. Query Intent Classification

```python
# AI Decision Logic
def classify_user_intent(query: str) -> Dict[str, float]:
    """
    Returns confidence scores for different intent categories
    """
    intents = {
        "stock_price_current": 0.0,
        "stock_price_historical": 0.0,
        "crypto_price": 0.0,
        "news_sentiment": 0.0,
        "economic_indicators": 0.0,
        "compliance_check": 0.0,
        "company_info": 0.0,
        "market_overview": 0.0
    }

    query_lower = query.lower()

    # Stock price patterns
    if any(word in query_lower for word in ["current", "now", "today", "live", "real-time"]):
        if any(word in query_lower for word in ["price", "quote", "trading", "stock"]):
            intents["stock_price_current"] = 0.9

    if any(word in query_lower for word in ["history", "past", "chart", "trend", "last month"]):
        intents["stock_price_historical"] = 0.85

    # Crypto patterns
    crypto_keywords = ["bitcoin", "btc", "ethereum", "eth", "crypto", "cryptocurrency"]
    if any(word in query_lower for word in crypto_keywords):
        intents["crypto_price"] = 0.9

    # News/Sentiment patterns
    if any(word in query_lower for word in ["news", "sentiment", "opinion", "what do people think"]):
        intents["news_sentiment"] = 0.8

    # Economic patterns
    economic_keywords = ["unemployment", "gdp", "inflation", "fed rate", "economy", "economic"]
    if any(word in query_lower for word in economic_keywords):
        intents["economic_indicators"] = 0.9

    # Compliance patterns
    compliance_keywords = ["sanctions", "compliance", "aml", "risk", "screening", "blacklist"]
    if any(word in query_lower for word in compliance_keywords):
        intents["compliance_check"] = 0.95

    return intents
```

### 2. API Selection Matrix

| User Query Type | Primary API | Function | Confidence | Fallback |
|-----------------|-------------|----------|------------|-----------|
| "AAPL stock price" | Alpha Vantage | GLOBAL_QUOTE | 0.9 | MarketStack |
| "AAPL price last month" | MarketStack | eod | 0.85 | Alpha Vantage |
| "Bitcoin price" | CoinGecko | simple_price | 0.95 | None |
| "Apple news" | News API | everything | 0.8 | None |
| "Unemployment rate" | FRED | series_observations | 0.9 | None |
| "Is John Smith sanctioned?" | OpenSanctions | search | 0.98 | None |

### 3. Response Processing Templates

#### Stock Price Response
```python
def process_stock_response(api_response: dict, symbol: str) -> dict:
    """
    Standardize stock price responses across different APIs
    """
    if "Global Quote" in api_response:  # Alpha Vantage
        quote = api_response["Global Quote"]
        return {
            "symbol": quote.get("01. symbol"),
            "current_price": float(quote.get("05. price", 0)),
            "change": float(quote.get("09. change", 0)),
            "change_percent": quote.get("10. change percent", "0%"),
            "volume": int(quote.get("06. volume", 0)),
            "source": "Alpha Vantage",
            "timestamp": quote.get("07. latest trading day"),
            "ai_interpretation": interpret_price_movement(float(quote.get("09. change", 0)))
        }
    elif "data" in api_response:  # MarketStack
        data = api_response["data"][0] if api_response["data"] else {}
        change = data.get("close", 0) - data.get("open", 0)
        return {
            "symbol": data.get("symbol"),
            "current_price": data.get("close"),
            "change": change,
            "change_percent": f"{(change/data.get('open', 1)*100):.2f}%",
            "volume": data.get("volume"),
            "source": "MarketStack",
            "timestamp": data.get("date"),
            "ai_interpretation": interpret_price_movement(change)
        }

def interpret_price_movement(change: float) -> str:
    """AI interpretation of price movement"""
    if change > 0:
        return "positive_movement" if change > 1 else "slight_positive"
    elif change < 0:
        return "negative_movement" if change < -1 else "slight_negative"
    else:
        return "no_change"
```

#### News Sentiment Response
```python
def process_news_sentiment(articles: list, symbol: str = None) -> dict:
    """
    Process news articles and extract sentiment
    """
    positive_keywords = ["surge", "gain", "profit", "growth", "rise", "bullish", "strong", "beat", "exceed"]
    negative_keywords = ["fall", "loss", "decline", "crash", "bearish", "weak", "drop", "miss", "disappoint"]

    sentiment_scores = []

    for article in articles:
        text = (article.get("title", "") + " " + article.get("description", "")).lower()

        positive_count = sum(1 for word in positive_keywords if word in text)
        negative_count = sum(1 for word in negative_keywords if word in text)

        if positive_count > negative_count:
            sentiment = "positive"
            score = min(positive_count / 10, 1.0)
        elif negative_count > positive_count:
            sentiment = "negative"
            score = -min(negative_count / 10, 1.0)
        else:
            sentiment = "neutral"
            score = 0.0

        sentiment_scores.append({
            "title": article.get("title"),
            "sentiment": sentiment,
            "score": score,
            "published": article.get("publishedAt"),
            "source": article.get("source", {}).get("name")
        })

    # Calculate overall sentiment
    avg_score = sum(item["score"] for item in sentiment_scores) / len(sentiment_scores)

    overall_sentiment = "neutral"
    if avg_score > 0.1:
        overall_sentiment = "positive"
    elif avg_score < -0.1:
        overall_sentiment = "negative"

    return {
        "overall_sentiment": overall_sentiment,
        "average_score": avg_score,
        "article_count": len(articles),
        "detailed_analysis": sentiment_scores,
        "ai_summary": generate_sentiment_summary(overall_sentiment, avg_score, len(articles))
    }

def generate_sentiment_summary(sentiment: str, score: float, count: int) -> str:
    """Generate human-readable sentiment summary"""
    if sentiment == "positive":
        return f"Market sentiment appears positive based on {count} recent articles (score: {score:.2f})"
    elif sentiment == "negative":
        return f"Market sentiment appears negative based on {count} recent articles (score: {score:.2f})"
    else:
        return f"Market sentiment appears neutral based on {count} recent articles"
```

### 4. Multi-API Orchestration Patterns

#### Complete Stock Analysis
```python
async def complete_stock_analysis(symbol: str) -> dict:
    """
    Orchestrate multiple APIs for comprehensive stock analysis
    """
    tasks = [
        get_current_price(symbol),  # Alpha Vantage
        get_recent_news(symbol),    # News API
        get_technical_indicators(symbol),  # Alpha Vantage RSI
        get_company_info(symbol)    # Alpha Vantage Overview
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    analysis = {
        "symbol": symbol,
        "timestamp": datetime.utcnow().isoformat(),
        "price_data": results[0] if not isinstance(results[0], Exception) else None,
        "sentiment_analysis": results[1] if not isinstance(results[1], Exception) else None,
        "technical_analysis": results[2] if not isinstance(results[2], Exception) else None,
        "company_info": results[3] if not isinstance(results[3], Exception) else None,
        "ai_recommendation": generate_ai_recommendation(results)
    }

    return analysis

def generate_ai_recommendation(analysis_results: list) -> dict:
    """Generate AI-based investment recommendation"""
    price_data, news_sentiment, technical_data, company_info = analysis_results

    recommendation_score = 0.0
    factors = []

    # Price momentum factor
    if price_data and "change" in price_data:
        change = price_data["change"]
        if change > 0:
            recommendation_score += 0.2
            factors.append("positive_price_momentum")
        else:
            recommendation_score -= 0.2
            factors.append("negative_price_momentum")

    # Sentiment factor
    if news_sentiment and "average_score" in news_sentiment:
        sentiment_score = news_sentiment["average_score"]
        recommendation_score += sentiment_score * 0.3
        factors.append(f"news_sentiment_{news_sentiment['overall_sentiment']}")

    # Technical factor (RSI)
    if technical_data and "RSI" in technical_data:
        rsi_value = float(technical_data["RSI"])
        if rsi_value < 30:  # Oversold
            recommendation_score += 0.3
            factors.append("technically_oversold")
        elif rsi_value > 70:  # Overbought
            recommendation_score -= 0.3
            factors.append("technically_overbought")

    # Generate recommendation
    if recommendation_score > 0.3:
        recommendation = "BUY"
        confidence = min(recommendation_score, 1.0)
    elif recommendation_score < -0.3:
        recommendation = "SELL"
        confidence = min(abs(recommendation_score), 1.0)
    else:
        recommendation = "HOLD"
        confidence = 1.0 - abs(recommendation_score)

    return {
        "recommendation": recommendation,
        "confidence": confidence,
        "score": recommendation_score,
        "factors": factors,
        "disclaimer": "This is an AI-generated recommendation and should not be considered as financial advice"
    }
```

### 5. Error Handling and Fallback Logic

```python
class APIOrchestrator:
    def __init__(self):
        self.api_status = {
            "alpha_vantage": {"available": True, "last_error": None, "rate_limit_reset": None},
            "marketstack": {"available": True, "last_error": None, "rate_limit_reset": None},
            "news_api": {"available": True, "last_error": None, "rate_limit_reset": None},
            "coingecko": {"available": True, "last_error": None, "rate_limit_reset": None},
            "fred": {"available": True, "last_error": None, "rate_limit_reset": None},
            "opensanctions": {"available": True, "last_error": None, "rate_limit_reset": None}
        }

    async def smart_api_call(self, primary_api: str, fallback_api: str = None, **kwargs) -> dict:
        """
        Intelligent API calling with fallback logic
        """
        try:
            # Check if primary API is available
            if not self.api_status[primary_api]["available"]:
                if fallback_api and self.api_status[fallback_api]["available"]:
                    return await self.call_api(fallback_api, **kwargs)
                else:
                    return await self.use_cached_or_mock_data(**kwargs)

            # Try primary API
            result = await self.call_api(primary_api, **kwargs)
            self.api_status[primary_api]["available"] = True
            return result

        except RateLimitError:
            self.api_status[primary_api]["available"] = False
            self.api_status[primary_api]["rate_limit_reset"] = time.time() + 3600

            if fallback_api:
                return await self.call_api(fallback_api, **kwargs)
            else:
                return await self.use_cached_or_mock_data(**kwargs)

        except APIError as e:
            self.api_status[primary_api]["last_error"] = str(e)

            if fallback_api:
                return await self.call_api(fallback_api, **kwargs)
            else:
                return {"error": f"API unavailable: {e}", "using_fallback": True}

    async def use_cached_or_mock_data(self, **kwargs) -> dict:
        """
        Return cached data or generate mock data as last resort
        """
        # Try cache first
        cached_data = await self.get_cached_data(**kwargs)
        if cached_data:
            cached_data["data_source"] = "cached"
            cached_data["cache_age"] = "recent"
            return cached_data

        # Generate mock data if no cache available
        mock_data = self.generate_mock_data(**kwargs)
        mock_data["data_source"] = "mock"
        mock_data["warning"] = "This is simulated data due to API unavailability"
        return mock_data
```

### 6. Response Confidence Scoring

```python
def calculate_response_confidence(api_response: dict, query_context: dict) -> float:
    """
    Calculate confidence score for API response
    """
    confidence = 0.0

    # Data freshness (newer = higher confidence)
    if "timestamp" in api_response:
        age_hours = (datetime.utcnow() - datetime.fromisoformat(api_response["timestamp"])).total_seconds() / 3600
        if age_hours < 1:
            confidence += 0.3  # Very fresh
        elif age_hours < 24:
            confidence += 0.2  # Recent
        elif age_hours < 168:  # 1 week
            confidence += 0.1  # Acceptable

    # Data completeness
    required_fields = query_context.get("required_fields", [])
    if required_fields:
        completeness = sum(1 for field in required_fields if field in api_response) / len(required_fields)
        confidence += completeness * 0.3

    # API reliability
    api_source = api_response.get("data_source", "unknown")
    source_reliability = {
        "Alpha Vantage": 0.9,
        "MarketStack": 0.8,
        "News API": 0.85,
        "CoinGecko": 0.9,
        "FRED": 0.95,
        "OpenSanctions": 0.9,
        "cached": 0.6,
        "mock": 0.1
    }
    confidence += source_reliability.get(api_source, 0.5) * 0.4

    return min(confidence, 1.0)
```

This guide enables AI agents to automatically select appropriate APIs, process responses intelligently, handle errors gracefully, and provide confidence-scored results to users.