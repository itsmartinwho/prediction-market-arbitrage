from __future__ import annotations
"""Real market activity using Polymarket Gamma Events API."""
import logging
from datetime import datetime, timedelta
from typing import Optional, List
from pydantic import BaseModel

from app.clients.polymarket.gamma_client import GammaClient, Event
from app.core.news_fetcher import get_news_fetcher, NewsArticle

logger = logging.getLogger(__name__)


class EventNews(BaseModel):
    """A news article related to an event."""
    title: str
    source: str
    url: str


class EventSummary(BaseModel):
    """An event summary for display (one entry per Polymarket event)."""
    id: str
    title: str
    slug: str
    yes_price: Optional[float] = None
    no_price: Optional[float] = None
    volume: float = 0.0
    liquidity: float = 0.0
    end_date: Optional[datetime] = None
    market_count: int = 1
    polymarket_url: str = ""
    news: Optional[EventNews] = None


class MarketActivity:
    """
    Provides real market activity data from Polymarket.

    Uses the Gamma Events API to fetch:
    - Hot events (highest volume)
    - Price movers (events with extreme prices)
    - Events closing soon

    Returns one entry per event (no duplicates).
    """

    def __init__(self):
        self.gamma = GammaClient()
        self._cache: Optional[List[Event]] = None
        self._cache_time: Optional[datetime] = None
        self._cache_ttl = timedelta(seconds=30)

    async def _get_events(self, force_refresh: bool = False) -> List[Event]:
        """Get events with caching."""
        now = datetime.utcnow()

        if (not force_refresh
            and self._cache is not None
            and self._cache_time is not None
            and now - self._cache_time < self._cache_ttl):
            return self._cache

        try:
            events = await self.gamma.get_all_active_events(max_events=300)
            self._cache = events
            self._cache_time = now
            logger.info(f"Fetched {len(events)} active events from Gamma Events API")
            return events
        except Exception as e:
            logger.error(f"Failed to fetch events: {e}")
            return self._cache or []

    def _event_to_summary(self, event: Event, news: Optional[EventNews] = None) -> EventSummary:
        """Convert Event to EventSummary for display."""
        return EventSummary(
            id=event.id,
            title=event.title,
            slug=event.slug,
            yes_price=event.yes_price,
            no_price=event.no_price,
            volume=event.volume or 0.0,
            liquidity=event.liquidity or 0.0,
            end_date=event.end_date,
            market_count=event.market_count,
            polymarket_url=event.polymarket_url,
            news=news,
        )

    async def _enrich_with_news(self, events: List[Event], limit: int) -> List[EventSummary]:
        """Convert events to summaries and fetch news for each."""
        import asyncio
        news_fetcher = get_news_fetcher()
        summaries = []

        # Fetch news for all events in parallel (with limit)
        async def get_news_for_event(event: Event) -> EventSummary:
            try:
                articles = await news_fetcher.get_news_for_market(event.title, limit=1)
                news = None
                if articles:
                    article = articles[0]
                    news = EventNews(
                        title=article.title,
                        source=article.source,
                        url=article.url,
                    )
                return self._event_to_summary(event, news)
            except Exception as e:
                logger.warning(f"Failed to fetch news for '{event.title}': {e}")
                return self._event_to_summary(event)

        # Process events in parallel batches of 5 to avoid overwhelming the API
        batch_size = 5
        for i in range(0, min(len(events), limit), batch_size):
            batch = events[i:i + batch_size]
            batch_results = await asyncio.gather(*[get_news_for_event(e) for e in batch])
            summaries.extend(batch_results)

        return summaries[:limit]

    async def get_hot_markets(self, limit: int = 20, include_news: bool = True) -> List[EventSummary]:
        """
        Get events with highest trading volume.

        These are the most actively traded events.
        """
        events = await self._get_events()

        # Already sorted by volume from the API
        if include_news:
            return await self._enrich_with_news(events, limit)
        return [self._event_to_summary(e) for e in events[:limit]]

    async def get_price_movers(self, limit: int = 20, include_news: bool = True) -> List[EventSummary]:
        """
        Get events with most extreme prices (furthest from 50/50).

        Events where YES or NO is trading far from 0.50 indicate
        strong market conviction.
        """
        events = await self._get_events()

        def price_extremity(e: Event) -> float:
            """How far is YES price from 0.50?"""
            if e.yes_price is None:
                return 0
            return abs(e.yes_price - 0.5)

        # Sort by how extreme the price is
        sorted_events = sorted(
            [e for e in events if e.yes_price is not None],
            key=price_extremity,
            reverse=True
        )

        if include_news:
            return await self._enrich_with_news(sorted_events, limit)
        return [self._event_to_summary(e) for e in sorted_events[:limit]]

    async def get_closing_soon(self, days: int = 7, limit: int = 20, include_news: bool = True) -> List[EventSummary]:
        """
        Get events closing within the specified number of days.

        These are time-sensitive opportunities.
        """
        events = await self._get_events()
        now = datetime.utcnow()
        cutoff = now + timedelta(days=days)

        # Filter to events with end_date within range
        closing_events = []
        for e in events:
            if e.end_date:
                # Handle timezone-aware datetimes
                end = e.end_date
                if hasattr(end, 'replace'):
                    end_naive = end.replace(tzinfo=None)
                else:
                    end_naive = end

                if now < end_naive < cutoff:
                    closing_events.append(e)

        # Sort by end_date ascending (soonest first)
        closing_events.sort(
            key=lambda e: e.end_date if e.end_date else datetime.max
        )

        if include_news:
            return await self._enrich_with_news(closing_events, limit)
        return [self._event_to_summary(e) for e in closing_events[:limit]]

    async def get_new_markets(self, limit: int = 20) -> List[EventSummary]:
        """
        Get recently created events.

        Returns events with lowest volume as a proxy for "new" events.
        """
        events = await self._get_events()

        # Sort by volume ascending (lowest volume = likely newer)
        sorted_events = sorted(
            events,
            key=lambda e: e.volume or float('inf')
        )

        # Filter out zero-volume events
        active_events = [e for e in sorted_events if (e.volume or 0) > 0]

        return [self._event_to_summary(e) for e in active_events[:limit]]

    async def search_markets(self, query: str, limit: int = 20, include_news: bool = True) -> List[EventSummary]:
        """
        Search events by keyword in title.

        Simple text search - matches if query appears in event title.
        """
        events = await self._get_events()
        query_lower = query.lower().strip()

        if not query_lower:
            return []

        matching = [
            e for e in events
            if query_lower in (e.title or "").lower()
        ]

        # Sort matches by volume (most liquid first)
        matching.sort(key=lambda e: e.volume or 0, reverse=True)

        if include_news:
            return await self._enrich_with_news(matching, limit)
        return [self._event_to_summary(e) for e in matching[:limit]]

    async def close(self):
        """Close the client."""
        await self.gamma.close()
