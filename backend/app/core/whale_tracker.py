from __future__ import annotations
"""Large recent trades on Polymarket, from the Data API."""
import logging
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.clients.polymarket.data_client import DataClient, Trade
from app.clients.polymarket.http import session
from app.config import get_settings
from app.core.cache import TTLCache, shared_cache

logger = logging.getLogger(__name__)

MAX_TRADES = 100


class WhaleActivity(BaseModel):
    """A large trade from Polymarket (whale activity)."""
    trader_name: str
    trader_address: Optional[str] = None
    market_question: str
    market_slug: str
    action: str  # "BUY" or "SELL"
    outcome: str  # "Yes", "No", or a named outcome
    size: float  # Number of shares
    price: float  # Price per share
    usd_value: float  # Total USD value
    timestamp: datetime  # when the trade happened (UTC)
    polymarket_url: str
    transaction_hash: Optional[str] = None


def trade_to_activity(trade: Trade) -> WhaleActivity:
    return WhaleActivity(
        trader_name=trade.trader_display_name,
        trader_address=trade.proxy_wallet,
        market_question=trade.title,
        market_slug=trade.slug,
        action=trade.side,
        outcome=trade.outcome,
        size=trade.size,
        price=trade.price,
        usd_value=trade.usd_value,
        timestamp=trade.timestamp,
        polymarket_url=trade.polymarket_url,
        transaction_hash=trade.transaction_hash,
    )


async def recent_large_trades(
    min_usd: float,
    limit: int,
    cache: Optional[TTLCache] = None,
    http=None,
) -> List[Trade]:
    """The latest trades of at least `min_usd`, newest first. Cached per (min, limit)."""
    cache = cache or shared_cache()
    limit = max(1, min(limit, MAX_TRADES))

    async def compute() -> List[Trade]:
        async with session(http) as client:
            trades = await DataClient(http=client).get_recent_trades(limit=limit, min_usd_amount=min_usd)
        trades.sort(key=lambda t: t.timestamp, reverse=True)
        return trades

    entry = await cache.get(f"trades:{min_usd:.0f}:{limit}", get_settings().cache_ttl_seconds, compute)
    return entry.value


class WhaleTracker:
    """Recent large trades, largest first."""

    def __init__(self, min_whale_usd: float = 1000, cache: Optional[TTLCache] = None):
        self.min_whale_usd = min_whale_usd
        self.cache = cache

    async def get_recent_whale_activity(self, limit: int = 20, min_usd: Optional[float] = None) -> List[WhaleActivity]:
        """The largest of the latest trades of at least `min_usd` (default $1,000)."""
        minimum = self.min_whale_usd if min_usd is None else min_usd
        trades = await recent_large_trades(minimum, limit * 2, cache=self.cache)
        activities = [trade_to_activity(t) for t in trades]
        activities.sort(key=lambda a: a.usd_value, reverse=True)
        return activities[:limit]

    async def get_top_movers(self, limit: int = 10) -> List[WhaleActivity]:
        """The largest recent trades of $5,000 or more."""
        return await self.get_recent_whale_activity(limit=limit, min_usd=5000)
