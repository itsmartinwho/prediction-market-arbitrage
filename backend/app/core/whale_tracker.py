from __future__ import annotations
"""Whale tracker for monitoring large trades on Polymarket using real Data API."""
import logging
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

from app.clients.polymarket.data_client import DataClient, Trade

logger = logging.getLogger(__name__)


class WhaleActivity(BaseModel):
    """A large trade from Polymarket (whale activity)."""
    trader_name: str
    trader_address: Optional[str] = None
    market_question: str
    market_slug: str
    action: str  # "BUY" or "SELL"
    outcome: str  # "Yes" or "No"
    size: float  # Number of shares
    price: float  # Price per share
    usd_value: float  # Total USD value
    timestamp: datetime
    polymarket_url: str
    transaction_hash: Optional[str] = None


class WhaleTracker:
    """
    Tracks large trades on Polymarket using the real Data API.

    Uses the Polymarket Data API to:
    - Get recent large trades (whale activity)
    - Filter by minimum USD value
    - Show who's moving markets
    """

    def __init__(self, min_whale_usd: float = 1000):
        """
        Initialize the whale tracker.

        Args:
            min_whale_usd: Minimum USD value to consider a trade as "whale" activity
        """
        self.data_client = DataClient()
        self.min_whale_usd = min_whale_usd

    async def close(self):
        """Close the data client."""
        await self.data_client.close()

    def _trade_to_activity(self, trade: Trade) -> WhaleActivity:
        """Convert a Trade to WhaleActivity."""
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

    async def get_recent_whale_activity(
        self,
        limit: int = 20,
        min_usd: Optional[float] = None,
    ) -> List[WhaleActivity]:
        """
        Get recent large trades (whale activity).

        Args:
            limit: Maximum number of trades to return
            min_usd: Minimum USD value (defaults to self.min_whale_usd)

        Returns:
            List of WhaleActivity sorted by USD value descending
        """
        min_amount = min_usd if min_usd is not None else self.min_whale_usd

        try:
            trades = await self.data_client.get_large_trades(
                min_usd=min_amount,
                limit=limit * 2,  # Fetch extra to account for filtering
            )

            # Convert to WhaleActivity
            activities = [self._trade_to_activity(t) for t in trades]

            # Sort by USD value descending
            activities.sort(key=lambda a: a.usd_value, reverse=True)

            return activities[:limit]

        except Exception as e:
            logger.error(f"Failed to fetch whale activity: {e}")
            return []

    async def get_whale_activity_for_market(
        self,
        condition_id: str,
        limit: int = 20,
    ) -> List[WhaleActivity]:
        """
        Get whale activity for a specific market.

        Args:
            condition_id: The market condition ID
            limit: Maximum number of trades to return

        Returns:
            List of WhaleActivity for the market
        """
        try:
            trades = await self.data_client.get_trades_for_market(
                condition_id=condition_id,
                limit=limit,
            )

            # Filter to larger trades and convert
            activities = [
                self._trade_to_activity(t)
                for t in trades
                if t.usd_value >= self.min_whale_usd
            ]

            return activities

        except Exception as e:
            logger.error(f"Failed to fetch whale activity for market: {e}")
            return []

    async def get_top_movers(self, limit: int = 10) -> List[WhaleActivity]:
        """
        Get the biggest trades in terms of USD value.

        This shows who's really moving the market.
        """
        return await self.get_recent_whale_activity(
            limit=limit,
            min_usd=5000,  # Higher threshold for "top movers"
        )
