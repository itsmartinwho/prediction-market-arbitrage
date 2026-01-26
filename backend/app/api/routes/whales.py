from __future__ import annotations
"""Whale tracking endpoints - real large trades from Polymarket Data API."""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel

from app.core.whale_tracker import WhaleTracker, WhaleActivity

router = APIRouter(prefix="/whales", tags=["whales"])

# Global tracker instance
_tracker: WhaleTracker | None = None


def get_tracker() -> WhaleTracker:
    global _tracker
    if _tracker is None:
        _tracker = WhaleTracker(min_whale_usd=1000)
    return _tracker


class WhaleActivityResponse(BaseModel):
    """Response model for whale activity (large trades)."""
    trader_name: str
    trader_address: Optional[str] = None
    market_question: str
    market_slug: str
    action: str  # BUY or SELL
    outcome: str  # Yes or No
    size: float  # Number of shares
    price: float  # Price per share
    usd_value: float  # Total USD value
    timestamp: datetime
    polymarket_url: str
    transaction_hash: Optional[str] = None


@router.get("/activity", response_model=list[WhaleActivityResponse])
async def get_whale_activity(limit: int = 20, min_usd: float = 1000):
    """
    Get recent large trades (whale activity) from Polymarket.

    This shows real trades happening on the platform, filtered to larger values.
    Each trade includes the trader's name (if available), market details, and
    a direct link to trade on Polymarket.

    Args:
        limit: Maximum number of trades to return (default: 20)
        min_usd: Minimum USD value to include (default: $1000)
    """
    tracker = get_tracker()
    activities = await tracker.get_recent_whale_activity(limit=limit, min_usd=min_usd)

    return [
        WhaleActivityResponse(
            trader_name=a.trader_name,
            trader_address=a.trader_address,
            market_question=a.market_question,
            market_slug=a.market_slug,
            action=a.action,
            outcome=a.outcome,
            size=a.size,
            price=a.price,
            usd_value=a.usd_value,
            timestamp=a.timestamp,
            polymarket_url=a.polymarket_url,
            transaction_hash=a.transaction_hash,
        )
        for a in activities
    ]


@router.get("/top-movers", response_model=list[WhaleActivityResponse])
async def get_top_movers(limit: int = 10):
    """
    Get the biggest trades by USD value.

    Shows who's really moving markets with large positions.
    """
    tracker = get_tracker()
    activities = await tracker.get_top_movers(limit=limit)

    return [
        WhaleActivityResponse(
            trader_name=a.trader_name,
            trader_address=a.trader_address,
            market_question=a.market_question,
            market_slug=a.market_slug,
            action=a.action,
            outcome=a.outcome,
            size=a.size,
            price=a.price,
            usd_value=a.usd_value,
            timestamp=a.timestamp,
            polymarket_url=a.polymarket_url,
            transaction_hash=a.transaction_hash,
        )
        for a in activities
    ]
