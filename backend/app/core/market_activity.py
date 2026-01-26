from __future__ import annotations
"""Real market activity using Polymarket Gamma API."""
import logging
from datetime import datetime, timedelta
from typing import Optional, List
from pydantic import BaseModel

from app.clients.polymarket.gamma_client import GammaClient
from app.models.market import Market

logger = logging.getLogger(__name__)


class MarketSummary(BaseModel):
    """A market summary for display."""
    id: str
    question: str
    slug: Optional[str] = None
    yes_price: Optional[float] = None
    no_price: Optional[float] = None
    volume: float = 0.0
    liquidity: float = 0.0
    end_date: Optional[datetime] = None
    polymarket_url: str = ""


class MarketActivity:
    """
    Provides real market activity data from Polymarket.

    Uses the Gamma API to fetch:
    - Hot markets (highest volume)
    - Price movers (significant price changes implied by YES/NO imbalance)
    - Markets closing soon
    """

    def __init__(self):
        self.gamma = GammaClient()
        self._cache: Optional[List[Market]] = None
        self._cache_time: Optional[datetime] = None
        self._cache_ttl = timedelta(seconds=30)

    async def _get_markets(self, force_refresh: bool = False) -> List[Market]:
        """Get markets with caching."""
        now = datetime.utcnow()

        if (not force_refresh
            and self._cache is not None
            and self._cache_time is not None
            and now - self._cache_time < self._cache_ttl):
            return self._cache

        try:
            markets = await self.gamma.get_all_active_markets()
            self._cache = markets
            self._cache_time = now
            logger.info(f"Fetched {len(markets)} active markets from Gamma API")
            return markets
        except Exception as e:
            logger.error(f"Failed to fetch markets: {e}")
            return self._cache or []

    def _market_to_summary(self, market: Market) -> MarketSummary:
        """Convert Market to MarketSummary."""
        # Build Polymarket URL
        slug = market.slug or market.id
        polymarket_url = f"https://polymarket.com/event/{slug}"

        return MarketSummary(
            id=market.id,
            question=market.question,
            slug=market.slug,
            yes_price=market.yes_price,
            no_price=market.no_price,
            volume=market.volume or 0.0,
            liquidity=market.liquidity or 0.0,
            end_date=market.end_date,
            polymarket_url=polymarket_url,
        )

    async def get_hot_markets(self, limit: int = 20) -> List[MarketSummary]:
        """
        Get markets with highest trading volume.

        These are the most actively traded markets.
        """
        markets = await self._get_markets()

        # Sort by volume descending
        sorted_markets = sorted(
            markets,
            key=lambda m: m.volume or 0,
            reverse=True
        )

        return [self._market_to_summary(m) for m in sorted_markets[:limit]]

    async def get_price_movers(self, limit: int = 20) -> List[MarketSummary]:
        """
        Get markets with most extreme prices (furthest from 50/50).

        Markets where YES or NO is trading far from 0.50 indicate
        strong market conviction. This is a proxy for "price movement"
        since we don't have historical price data.
        """
        markets = await self._get_markets()

        def price_extremity(m: Market) -> float:
            """How far is YES price from 0.50?"""
            if m.yes_price is None:
                return 0
            return abs(m.yes_price - 0.5)

        # Sort by how extreme the price is
        sorted_markets = sorted(
            markets,
            key=price_extremity,
            reverse=True
        )

        return [self._market_to_summary(m) for m in sorted_markets[:limit]]

    async def get_closing_soon(self, days: int = 7, limit: int = 20) -> List[MarketSummary]:
        """
        Get markets closing within the specified number of days.

        These are time-sensitive opportunities.
        """
        markets = await self._get_markets()
        now = datetime.utcnow()
        cutoff = now + timedelta(days=days)

        # Filter to markets with end_date within range
        closing_markets = []
        for m in markets:
            if m.end_date:
                # Handle both datetime and string end_date
                end = m.end_date
                if isinstance(end, str):
                    try:
                        end = datetime.fromisoformat(end.replace('Z', '+00:00'))
                    except Exception:
                        continue

                # Check if within range (after now, before cutoff)
                if hasattr(end, 'replace'):
                    end_naive = end.replace(tzinfo=None)
                else:
                    end_naive = end

                if now < end_naive < cutoff:
                    closing_markets.append(m)

        # Sort by end_date ascending (soonest first)
        closing_markets.sort(
            key=lambda m: m.end_date if m.end_date else datetime.max
        )

        return [self._market_to_summary(m) for m in closing_markets[:limit]]

    async def get_new_markets(self, limit: int = 20) -> List[MarketSummary]:
        """
        Get recently created markets.

        Note: Gamma API doesn't provide creation date, so this returns
        markets with lowest volume as a proxy for "new" markets.
        """
        markets = await self._get_markets()

        # Sort by volume ascending (lowest volume = likely newer)
        sorted_markets = sorted(
            markets,
            key=lambda m: m.volume or float('inf')
        )

        # Filter out zero-volume markets (might be broken)
        active_markets = [m for m in sorted_markets if (m.volume or 0) > 0]

        return [self._market_to_summary(m) for m in active_markets[:limit]]

    async def search_markets(self, query: str, limit: int = 20) -> List[MarketSummary]:
        """
        Search markets by keyword in question.

        Simple text search - matches if query appears in market question.
        """
        markets = await self._get_markets()
        query_lower = query.lower().strip()

        if not query_lower:
            return []

        matching = [
            m for m in markets
            if query_lower in (m.question or "").lower()
        ]

        # Sort matches by volume (most liquid first)
        matching.sort(key=lambda m: m.volume or 0, reverse=True)

        return [self._market_to_summary(m) for m in matching[:limit]]

    async def close(self):
        """Close the client."""
        await self.gamma.close()
