from __future__ import annotations
"""News front-runner endpoints."""
from datetime import datetime
from fastapi import APIRouter
from pydantic import BaseModel

from app.core.news_tracker import NewsTracker, NewsItem, MarketSignal

router = APIRouter(prefix="/news", tags=["news"])

# Global tracker instance
_tracker: NewsTracker | None = None


def get_tracker() -> NewsTracker:
    global _tracker
    if _tracker is None:
        _tracker = NewsTracker()
    return _tracker


class NewsItemResponse(BaseModel):
    id: str
    title: str
    summary: str
    source: str
    url: str
    published_at: datetime
    relevance_score: float
    sentiment: str
    related_markets: list[str]
    keywords: list[str]


class MarketSignalResponse(BaseModel):
    news_id: str
    news_title: str
    market_id: str
    market_question: str
    signal: str
    confidence: float
    current_price: float | None = None
    target_price: float | None = None
    reasoning: str
    detected_at: datetime


@router.get("", response_model=list[NewsItemResponse])
async def get_recent_news(limit: int = 20):
    """Get recent news relevant to prediction markets."""
    tracker = get_tracker()
    news = await tracker.fetch_recent_news(limit=limit)

    return [
        NewsItemResponse(
            id=n.id,
            title=n.title,
            summary=n.summary,
            source=n.source,
            url=n.url,
            published_at=n.published_at,
            relevance_score=n.relevance_score,
            sentiment=n.sentiment,
            related_markets=n.related_markets,
            keywords=n.keywords,
        )
        for n in news
    ]


@router.get("/signals", response_model=list[MarketSignalResponse])
async def get_trading_signals():
    """Get trading signals derived from news analysis."""
    tracker = get_tracker()

    # Fetch news first if not already done
    if not tracker.recent_news:
        await tracker.fetch_recent_news()

    signals = await tracker.generate_signals()

    return [
        MarketSignalResponse(
            news_id=s.news_id,
            news_title=s.news_title,
            market_id=s.market_id,
            market_question=s.market_question,
            signal=s.signal,
            confidence=s.confidence,
            current_price=s.current_price,
            target_price=s.target_price,
            reasoning=s.reasoning,
            detected_at=s.detected_at,
        )
        for s in signals
    ]


@router.post("/refresh")
async def refresh_news():
    """Force refresh news and signals."""
    tracker = get_tracker()
    news = await tracker.fetch_recent_news()
    signals = await tracker.generate_signals()

    return {
        "status": "refreshed",
        "news_count": len(news),
        "signals_count": len(signals),
    }
