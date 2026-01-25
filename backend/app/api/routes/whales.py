from __future__ import annotations
"""Whale tracking endpoints."""
from datetime import datetime
from fastapi import APIRouter
from pydantic import BaseModel

from app.core.whale_tracker import WhaleTracker, Whale, WhaleActivity, WhalePosition

router = APIRouter(prefix="/whales", tags=["whales"])

# Global tracker instance
_tracker: WhaleTracker | None = None


def get_tracker() -> WhaleTracker:
    global _tracker
    if _tracker is None:
        _tracker = WhaleTracker()
    return _tracker


class WhaleResponse(BaseModel):
    address: str
    name: str | None = None
    profit_loss: float
    volume: float
    positions_count: int
    win_rate: float | None = None


class WhaleActivityResponse(BaseModel):
    whale_address: str
    whale_name: str | None = None
    market_id: str
    market_question: str
    action: str
    outcome: str
    shares: float
    price: float
    timestamp: datetime
    usd_value: float


class WhalePositionResponse(BaseModel):
    market_id: str
    market_question: str
    outcome: str
    shares: float
    avg_price: float
    current_price: float | None = None
    pnl: float | None = None


@router.get("", response_model=list[WhaleResponse])
async def get_top_whales(limit: int = 10):
    """Get top traders by profit."""
    tracker = get_tracker()
    whales = await tracker.get_top_traders(limit=limit)

    return [
        WhaleResponse(
            address=w.address,
            name=w.name,
            profit_loss=w.profit_loss,
            volume=w.volume,
            positions_count=w.positions_count,
            win_rate=w.win_rate,
        )
        for w in whales
    ]


@router.get("/activity", response_model=list[WhaleActivityResponse])
async def get_whale_activity(limit: int = 20):
    """Get recent whale trading activity."""
    tracker = get_tracker()
    activities = await tracker.get_recent_whale_activity(limit=limit)

    return [
        WhaleActivityResponse(
            whale_address=a.whale_address,
            whale_name=a.whale_name,
            market_id=a.market_id,
            market_question=a.market_question,
            action=a.action,
            outcome=a.outcome,
            shares=a.shares,
            price=a.price,
            timestamp=a.timestamp,
            usd_value=a.usd_value,
        )
        for a in activities
    ]


@router.get("/{address}/positions", response_model=list[WhalePositionResponse])
async def get_whale_positions(address: str):
    """Get positions for a specific whale."""
    tracker = get_tracker()
    positions = await tracker.get_whale_positions(address)

    return [
        WhalePositionResponse(
            market_id=p.market_id,
            market_question=p.market_question,
            outcome=p.outcome,
            shares=p.shares,
            avg_price=p.avg_price,
            current_price=p.current_price,
            pnl=p.pnl,
        )
        for p in positions
    ]


@router.post("/{address}/watch")
async def watch_whale(address: str):
    """Add a whale to the watch list."""
    tracker = get_tracker()
    whales = await tracker.get_top_traders(limit=20)

    # Find the whale
    whale = next((w for w in whales if w.address == address), None)
    if whale:
        tracker.watch_whale(address, whale)
        return {"status": "watching", "address": address, "name": whale.name}

    return {"status": "not_found", "address": address}


@router.delete("/{address}/watch")
async def unwatch_whale(address: str):
    """Remove a whale from the watch list."""
    tracker = get_tracker()
    tracker.unwatch_whale(address)
    return {"status": "unwatched", "address": address}
