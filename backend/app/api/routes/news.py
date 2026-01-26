from __future__ import annotations
"""Market intelligence endpoints - real trading signals from Polymarket activity."""
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter
from pydantic import BaseModel

from app.core.market_intelligence import get_market_intelligence, MarketSignal as IntelSignal

router = APIRouter(prefix="/news", tags=["market-intelligence"])


class SignalResponse(BaseModel):
    """Response model for market signals."""

    id: str
    type: str  # "whale_trade", "price_spike", "volume_surge"
    title: str
    summary: str
    market_question: str
    market_url: str
    signal: str  # "BUY_YES", "BUY_NO", "SELL_YES", "SELL_NO", "WATCH"
    confidence: float
    current_price: Optional[float] = None
    reasoning: str
    detected_at: datetime


@router.get("", response_model=List[SignalResponse])
async def get_market_signals(limit: int = 20):
    """
    Get trading signals derived from real Polymarket activity.

    Signals are generated from:
    - Whale trades (large positions >$5K)
    - Extreme prices (strong conviction markets)
    - Volume surges (active markets)

    Each signal includes:
    - The market question and direct Polymarket URL
    - Signal type (BUY_YES, BUY_NO, etc.) and confidence
    - Reasoning explaining the signal
    """
    intel = get_market_intelligence()
    signals = await intel.get_signals(limit=limit)

    return [
        SignalResponse(
            id=s.id,
            type=s.type,
            title=s.title,
            summary=s.summary,
            market_question=s.market_question,
            market_url=s.market_url,
            signal=s.signal,
            confidence=s.confidence,
            current_price=s.current_price,
            reasoning=s.reasoning,
            detected_at=s.detected_at,
        )
        for s in signals
    ]


@router.get("/signals", response_model=List[SignalResponse])
async def get_trading_signals():
    """
    Alias for main signals endpoint (backward compatibility).

    Returns trading signals from market activity.
    """
    return await get_market_signals(limit=15)


@router.post("/refresh")
async def refresh_signals():
    """Force refresh of market intelligence signals."""
    intel = get_market_intelligence()
    signals = await intel.get_signals(limit=20)

    return {
        "status": "refreshed",
        "signals_count": len(signals),
        "signal_types": {
            "whale_trade": sum(1 for s in signals if s.type == "whale_trade"),
            "price_spike": sum(1 for s in signals if s.type == "price_spike"),
            "volume_surge": sum(1 for s in signals if s.type == "volume_surge"),
        },
    }
