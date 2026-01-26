from __future__ import annotations
"""Market activity endpoints - real data from Polymarket."""
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.core.market_activity import MarketActivity, MarketSummary

router = APIRouter(prefix="/market-activity", tags=["market-activity"])

# Global activity instance
_activity: Optional[MarketActivity] = None


def get_activity() -> MarketActivity:
    global _activity
    if _activity is None:
        _activity = MarketActivity()
    return _activity


class MarketResponse(BaseModel):
    """Market response for API."""
    id: str
    question: str
    slug: Optional[str] = None
    yes_price: Optional[float] = None
    no_price: Optional[float] = None
    volume: float = 0.0
    liquidity: float = 0.0
    end_date: Optional[datetime] = None
    polymarket_url: str = ""


class MarketListResponse(BaseModel):
    """Response wrapper with count."""
    markets: List[MarketResponse]
    count: int


def summary_to_response(s: MarketSummary) -> MarketResponse:
    return MarketResponse(
        id=s.id,
        question=s.question,
        slug=s.slug,
        yes_price=s.yes_price,
        no_price=s.no_price,
        volume=s.volume,
        liquidity=s.liquidity,
        end_date=s.end_date,
        polymarket_url=s.polymarket_url,
    )


@router.get("/hot", response_model=MarketListResponse)
async def get_hot_markets(limit: int = Query(default=20, ge=1, le=50)):
    """
    Get markets with highest trading volume.

    These are the most actively traded markets on Polymarket.
    """
    activity = get_activity()
    markets = await activity.get_hot_markets(limit=limit)

    return MarketListResponse(
        markets=[summary_to_response(m) for m in markets],
        count=len(markets),
    )


@router.get("/movers", response_model=MarketListResponse)
async def get_price_movers(limit: int = Query(default=20, ge=1, le=50)):
    """
    Get markets with most extreme prices.

    Markets where YES or NO is far from 50% indicate strong conviction.
    """
    activity = get_activity()
    markets = await activity.get_price_movers(limit=limit)

    return MarketListResponse(
        markets=[summary_to_response(m) for m in markets],
        count=len(markets),
    )


@router.get("/closing-soon", response_model=MarketListResponse)
async def get_closing_soon(
    days: int = Query(default=7, ge=1, le=30),
    limit: int = Query(default=20, ge=1, le=50)
):
    """
    Get markets closing within the specified number of days.

    Time-sensitive trading opportunities.
    """
    activity = get_activity()
    markets = await activity.get_closing_soon(days=days, limit=limit)

    return MarketListResponse(
        markets=[summary_to_response(m) for m in markets],
        count=len(markets),
    )


@router.get("/new", response_model=MarketListResponse)
async def get_new_markets(limit: int = Query(default=20, ge=1, le=50)):
    """
    Get recently created / low volume markets.

    New markets may have inefficient pricing.
    """
    activity = get_activity()
    markets = await activity.get_new_markets(limit=limit)

    return MarketListResponse(
        markets=[summary_to_response(m) for m in markets],
        count=len(markets),
    )


@router.get("/search", response_model=MarketListResponse)
async def search_markets(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(default=20, ge=1, le=50)
):
    """
    Search markets by keyword.

    Searches market questions for the given term.
    """
    activity = get_activity()
    markets = await activity.search_markets(query=q, limit=limit)

    return MarketListResponse(
        markets=[summary_to_response(m) for m in markets],
        count=len(markets),
    )
