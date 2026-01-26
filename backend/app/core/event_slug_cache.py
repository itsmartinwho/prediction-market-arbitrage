"""Cache for mapping market slugs to event slugs using Data API."""
from __future__ import annotations
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict

from app.clients.polymarket.data_client import DataClient

logger = logging.getLogger(__name__)


class EventSlugCache:
    """
    Caches event_slug mappings from Data API trades.

    The Data API provides eventSlug with each trade. We cache these
    to resolve URLs for markets from the Gamma API (which only has slug).

    This solves the URL problem:
    - Gamma API: slug = "will-trump-win-2024" (market slug)
    - Data API: eventSlug = "presidential-election-2024" (event slug)
    - Polymarket URL needs: event_slug
    """

    def __init__(self, ttl_minutes: int = 30):
        self.data_client = DataClient()
        self._condition_to_event: Dict[str, str] = {}  # condition_id -> event_slug
        self._slug_to_event: Dict[str, str] = {}  # market slug -> event_slug
        self._last_refresh: Optional[datetime] = None
        self._ttl = timedelta(minutes=ttl_minutes)

    async def refresh_cache(self, limit: int = 500) -> int:
        """
        Fetch recent trades to build slug mappings.

        Returns the number of new mappings added.
        """
        try:
            # Fetch recent trades - these include eventSlug
            trades = await self.data_client.get_recent_trades(limit=limit)
            added = 0

            for trade in trades:
                if trade.event_slug:
                    # Map condition_id -> event_slug
                    if trade.condition_id and trade.condition_id not in self._condition_to_event:
                        self._condition_to_event[trade.condition_id] = trade.event_slug
                        added += 1

                    # Map market slug -> event_slug
                    if trade.slug and trade.slug not in self._slug_to_event:
                        self._slug_to_event[trade.slug] = trade.event_slug
                        added += 1

            self._last_refresh = datetime.utcnow()
            logger.info(
                f"Event slug cache refreshed: {len(self._condition_to_event)} condition mappings, "
                f"{len(self._slug_to_event)} slug mappings"
            )
            return added

        except Exception as e:
            logger.error(f"Failed to refresh event slug cache: {e}")
            return 0

    async def _ensure_fresh(self):
        """Refresh cache if stale or empty."""
        if (
            self._last_refresh is None
            or datetime.utcnow() - self._last_refresh > self._ttl
        ):
            await self.refresh_cache()

    async def get_event_slug(
        self,
        condition_id: Optional[str] = None,
        market_slug: Optional[str] = None,
    ) -> Optional[str]:
        """
        Get event_slug from condition_id or market slug.

        Args:
            condition_id: The market's condition ID
            market_slug: The market's slug from Gamma API

        Returns:
            The event_slug if found, None otherwise
        """
        await self._ensure_fresh()

        # Try condition_id first (more reliable)
        if condition_id and condition_id in self._condition_to_event:
            return self._condition_to_event[condition_id]

        # Try market slug
        if market_slug and market_slug in self._slug_to_event:
            return self._slug_to_event[market_slug]

        return None

    def build_polymarket_url(
        self,
        condition_id: Optional[str] = None,
        market_slug: Optional[str] = None,
        fallback_slug: Optional[str] = None,
    ) -> str:
        """
        Build a Polymarket URL, using cached event_slug if available.

        This is a synchronous method that uses whatever is in the cache.
        Call _ensure_fresh() or get_event_slug() first if you need fresh data.

        Args:
            condition_id: The market's condition ID
            market_slug: The market's slug from Gamma API
            fallback_slug: Fallback slug to use if no mapping found

        Returns:
            A Polymarket URL, or empty string if no slug available
        """
        # Try condition_id first
        if condition_id and condition_id in self._condition_to_event:
            return f"https://polymarket.com/event/{self._condition_to_event[condition_id]}"

        # Try market slug
        if market_slug and market_slug in self._slug_to_event:
            return f"https://polymarket.com/event/{self._slug_to_event[market_slug]}"

        # Fallback to provided slug (may not work but better than nothing)
        if fallback_slug:
            return f"https://polymarket.com/event/{fallback_slug}"

        return ""

    async def build_polymarket_url_async(
        self,
        condition_id: Optional[str] = None,
        market_slug: Optional[str] = None,
        fallback_slug: Optional[str] = None,
    ) -> str:
        """
        Build a Polymarket URL, ensuring cache is fresh first.

        Async version that refreshes cache if needed.
        """
        await self._ensure_fresh()
        return self.build_polymarket_url(condition_id, market_slug, fallback_slug)

    @property
    def cache_size(self) -> int:
        """Return total number of cached mappings."""
        return len(self._condition_to_event) + len(self._slug_to_event)

    @property
    def is_stale(self) -> bool:
        """Check if cache needs refresh."""
        if self._last_refresh is None:
            return True
        return datetime.utcnow() - self._last_refresh > self._ttl

    async def close(self):
        """Close the data client."""
        await self.data_client.close()


# Global singleton instance
_cache_instance: Optional[EventSlugCache] = None


def get_event_slug_cache() -> EventSlugCache:
    """Get the global EventSlugCache singleton."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = EventSlugCache()
    return _cache_instance
