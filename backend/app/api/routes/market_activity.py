from __future__ import annotations
"""Market lists: hot, price movers, closing soon, quiet, and search."""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.core.market_activity import EventList, EventSummary, get_market_activity

router = APIRouter(prefix="/market-activity", tags=["market-activity"])


class NewsResponse(BaseModel):
    title: str
    source: str
    url: str


class EventResponse(BaseModel):
    """One Polymarket event page."""
    id: str
    title: str
    slug: str
    yes_price: Optional[float] = None
    no_price: Optional[float] = None
    volume: float = 0.0
    volume_24h: float = 0.0
    liquidity: float = 0.0
    end_date: Optional[datetime] = None
    market_count: int = 1
    polymarket_url: str = ""
    news: Optional[NewsResponse] = None


class EventListResponse(BaseModel):
    markets: List[EventResponse]
    count: int
    fetched_at: datetime  # when Gamma was last asked for this list


def _event(s: EventSummary) -> EventResponse:
    data = s.model_dump()
    data["news"] = NewsResponse(**s.news.model_dump()) if s.news else None
    return EventResponse(**data)


def _list(result: EventList) -> EventListResponse:
    return EventListResponse(
        markets=[_event(e) for e in result.markets],
        count=len(result.markets),
        fetched_at=result.fetched_at,
    )


@router.get("/hot", response_model=EventListResponse)
async def get_hot_markets(limit: int = Query(default=20, ge=1, le=50)):
    """Events with the most trading in the last 24 hours."""
    return _list(await get_market_activity().get_hot_markets(limit=limit))


@router.get("/movers", response_model=EventListResponse)
async def get_price_movers(limit: int = Query(default=20, ge=1, le=50)):
    """Of the hot events, those priced furthest from 50/50."""
    return _list(await get_market_activity().get_price_movers(limit=limit))


@router.get("/closing-soon", response_model=EventListResponse)
async def get_closing_soon(
    days: int = Query(default=7, ge=1, le=30),
    limit: int = Query(default=20, ge=1, le=50),
):
    """Events that end within `days`, soonest first."""
    return _list(await get_market_activity().get_closing_soon(days=days, limit=limit))


@router.get("/new", response_model=EventListResponse)
async def get_new_markets(limit: int = Query(default=20, ge=1, le=50)):
    """The quietest of the hot events (a rough stand-in for new ones)."""
    return _list(await get_market_activity().get_new_markets(limit=limit))


@router.get("/search", response_model=EventListResponse)
async def search_markets(
    q: str = Query(..., min_length=1, max_length=100, description="Search query"),
    limit: int = Query(default=20, ge=1, le=50),
):
    """Open events matching the query, by Gamma's search."""
    return _list(await get_market_activity().search_markets(query=q, limit=limit))
