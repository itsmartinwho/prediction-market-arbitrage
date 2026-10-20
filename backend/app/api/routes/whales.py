from __future__ import annotations
"""Whale endpoints: large recent trades from Polymarket's Data API."""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.core.whale_tracker import WhaleActivity, WhaleTracker

router = APIRouter(prefix="/whales", tags=["whales"])


class WhaleActivityResponse(BaseModel):
    trader_name: str
    trader_address: Optional[str] = None
    market_question: str
    market_slug: str
    action: str  # BUY or SELL
    outcome: str
    size: float  # shares
    price: float  # per share
    usd_value: float
    timestamp: datetime  # when the trade happened (UTC)
    polymarket_url: str
    transaction_hash: Optional[str] = None


def _responses(activities: List[WhaleActivity]) -> List[WhaleActivityResponse]:
    return [WhaleActivityResponse(**a.model_dump()) for a in activities]


@router.get("/activity", response_model=List[WhaleActivityResponse])
async def get_whale_activity(
    limit: int = Query(default=20, ge=1, le=50),
    min_usd: float = Query(default=1000, ge=0),
):
    """The largest of the latest trades worth at least `min_usd` (default $1,000)."""
    return _responses(await WhaleTracker().get_recent_whale_activity(limit=limit, min_usd=min_usd))


@router.get("/top-movers", response_model=List[WhaleActivityResponse])
async def get_top_movers(limit: int = Query(default=10, ge=1, le=50)):
    """The largest recent trades of $5,000 or more."""
    return _responses(await WhaleTracker().get_top_movers(limit=limit))
