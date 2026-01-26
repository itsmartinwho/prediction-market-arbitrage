from __future__ import annotations
"""Market activity endpoints - real data from Polymarket."""
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.core.market_activity import MarketActivity, EventSummary, EventNews

router = APIRouter(prefix="/market-activity", tags=["market-activity"])

# Global activity instance
_activity: Optional[MarketActivity] = None


def get_activity() -> MarketActivity:
    global _activity
    if _activity is None:
        _activity = MarketActivity()
    return _activity


class NewsResponse(BaseModel):
    """News article related to an event."""
    title: str
    source: str
    url: str


class EventResponse(BaseModel):
    """Event response for API (one entry per Polymarket event)."""
    id: str
    title: str
    slug: str
    yes_price: Optional[float] = None
    no_price: Optional[float] = None
    volume: float = 0.0
    liquidity: float = 0.0
    end_date: Optional[datetime] = None
    market_count: int = 1
    polymarket_url: str = ""
    news: Optional[NewsResponse] = None


class EventListResponse(BaseModel):
    """Response wrapper with count."""
    markets: List[EventResponse]
    count: int


def summary_to_response(s: EventSummary) -> EventResponse:
    news = None
    if s.news:
        news = NewsResponse(
            title=s.news.title,
            source=s.news.source,
            url=s.news.url,
        )
    return EventResponse(
        id=s.id,
        title=s.title,
        slug=s.slug,
        yes_price=s.yes_price,
        no_price=s.no_price,
        volume=s.volume,
        liquidity=s.liquidity,
        end_date=s.end_date,
        market_count=s.market_count,
        polymarket_url=s.polymarket_url,
        news=news,
    )


@router.get("/hot", response_model=EventListResponse)
async def get_hot_markets(limit: int = Query(default=20, ge=1, le=50)):
    """
    Get events with highest trading volume.

    These are the most actively traded events on Polymarket.
    Each entry represents one Polymarket event page (no duplicates).
    """
    activity = get_activity()
    events = await activity.get_hot_markets(limit=limit)

    return EventListResponse(
        markets=[summary_to_response(e) for e in events],
        count=len(events),
    )


@router.get("/movers", response_model=EventListResponse)
async def get_price_movers(limit: int = Query(default=20, ge=1, le=50)):
    """
    Get events with most extreme prices.

    Events where YES or NO is far from 50% indicate strong conviction.
    """
    activity = get_activity()
    events = await activity.get_price_movers(limit=limit)

    return EventListResponse(
        markets=[summary_to_response(e) for e in events],
        count=len(events),
    )


@router.get("/closing-soon", response_model=EventListResponse)
async def get_closing_soon(
    days: int = Query(default=7, ge=1, le=30),
    limit: int = Query(default=20, ge=1, le=50)
):
    """
    Get events closing within the specified number of days.

    Time-sensitive trading opportunities.
    """
    activity = get_activity()
    events = await activity.get_closing_soon(days=days, limit=limit)

    return EventListResponse(
        markets=[summary_to_response(e) for e in events],
        count=len(events),
    )


@router.get("/new", response_model=EventListResponse)
async def get_new_markets(limit: int = Query(default=20, ge=1, le=50)):
    """
    Get recently created / low volume events.

    New events may have inefficient pricing.
    """
    activity = get_activity()
    events = await activity.get_new_markets(limit=limit)

    return EventListResponse(
        markets=[summary_to_response(e) for e in events],
        count=len(events),
    )


@router.get("/search", response_model=EventListResponse)
async def search_markets(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(default=20, ge=1, le=50)
):
    """
    Search events by keyword.

    Searches event titles for the given term.
    """
    activity = get_activity()
    events = await activity.search_markets(query=q, limit=limit)

    return EventListResponse(
        markets=[summary_to_response(e) for e in events],
        count=len(events),
    )
