from __future__ import annotations
"""Market lists for the dashboard, from Polymarket's Gamma events API.

Every list is one Gamma request at most per cache TTL: hot and movers share
the top 100 events by 24-hour volume, closing soon asks Gamma for events that
end within the window, and search uses Gamma's own search. Each entry is one
Polymarket event page; the first few carry a recent headline when one
arrives in time.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from pydantic import BaseModel

from app.clients.polymarket.gamma_client import Event, GammaClient
from app.clients.polymarket.http import session
from app.config import get_settings
from app.core.cache import TTLCache, shared_cache
from app.core.news_fetcher import get_news_fetcher

logger = logging.getLogger(__name__)

TOP_EVENTS = 100  # one Gamma page


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
    volume_24h: float = 0.0
    liquidity: float = 0.0
    end_date: Optional[datetime] = None
    market_count: int = 1
    polymarket_url: str = ""
    news: Optional[EventNews] = None


class EventList(BaseModel):
    markets: List[EventSummary]
    fetched_at: datetime


class MarketActivity:
    def __init__(self, cache: Optional[TTLCache] = None, http=None):
        self.cache = cache or shared_cache()
        self.ttl = get_settings().cache_ttl_seconds
        self._http = http

    async def _events(self, key: str, fetch) -> tuple:
        """(events, fetched_at) from the cache, fetching when stale."""

        async def compute():
            async with session(self._http) as client:
                return await fetch(GammaClient(http=client))

        entry = await self.cache.get(key, self.ttl, compute)
        return entry.value, datetime.fromtimestamp(entry.stored_at, tz=timezone.utc)

    async def _top_events(self) -> tuple:
        return await self._events(
            "events:top24h", lambda gamma: gamma.get_events(limit=TOP_EVENTS, order="volume24hr")
        )

    @staticmethod
    def _summary(event: Event, news: Optional[EventNews] = None) -> EventSummary:
        return EventSummary(
            id=event.id,
            title=event.title,
            slug=event.slug,
            yes_price=event.yes_price,
            no_price=event.no_price,
            volume=event.volume or 0.0,
            volume_24h=event.volume_24h or 0.0,
            liquidity=event.liquidity or 0.0,
            end_date=event.end_date,
            market_count=event.market_count,
            polymarket_url=event.polymarket_url,
            news=news,
        )

    async def _with_news(self, events: List[Event], limit: int, include_news: bool) -> List[EventSummary]:
        events = events[:limit]
        headlines = {}
        if include_news and events:
            headlines = await get_news_fetcher().headlines_for(e.title for e in events)
        summaries = []
        for event in events:
            article = headlines.get(event.title)
            news = EventNews(title=article.title, source=article.source, url=article.url) if article else None
            summaries.append(self._summary(event, news))
        return summaries

    async def get_hot_markets(self, limit: int = 20, include_news: bool = True) -> EventList:
        """The events with the most trading in the last 24 hours."""
        events, fetched_at = await self._top_events()
        return EventList(markets=await self._with_news(events, limit, include_news), fetched_at=fetched_at)

    async def get_price_movers(self, limit: int = 20, include_news: bool = True) -> EventList:
        """Of the hot events, those priced furthest from 50/50."""
        events, fetched_at = await self._top_events()
        priced = [e for e in events if e.yes_price is not None]
        priced.sort(key=lambda e: abs((e.yes_price or 0.5) - 0.5), reverse=True)
        return EventList(markets=await self._with_news(priced, limit, include_news), fetched_at=fetched_at)

    async def get_closing_soon(self, days: int = 7, limit: int = 20, include_news: bool = True) -> EventList:
        """Events ending within `days`, soonest first."""

        async def fetch(gamma: GammaClient):
            now = datetime.now(timezone.utc)
            return await gamma.get_events(
                limit=TOP_EVENTS, order="volume24hr", end_date_min=now, end_date_max=now + timedelta(days=days)
            )

        events, fetched_at = await self._events(f"events:closing:{days}", fetch)
        now = datetime.now(timezone.utc)
        upcoming = [e for e in events if e.end_date and e.end_date > now]
        upcoming.sort(key=lambda e: e.end_date)
        return EventList(markets=await self._with_news(upcoming, limit, include_news), fetched_at=fetched_at)

    async def get_new_markets(self, limit: int = 20) -> EventList:
        """The lowest-volume hot events, a rough stand-in for new ones."""
        events, fetched_at = await self._top_events()
        quiet = sorted((e for e in events if (e.volume or 0) > 0), key=lambda e: e.volume or 0)
        return EventList(markets=[self._summary(e) for e in quiet[:limit]], fetched_at=fetched_at)

    async def search_markets(self, query: str, limit: int = 20, include_news: bool = True) -> EventList:
        """Open events matching `query`, by Gamma's search."""
        q = " ".join(query.lower().split())[:100]
        if not q:
            return EventList(markets=[], fetched_at=datetime.now(timezone.utc))
        events, fetched_at = await self._events(f"search:{q}", lambda gamma: gamma.search_events(q, limit=50))
        return EventList(markets=await self._with_news(events, limit, include_news), fetched_at=fetched_at)


_activity: Optional[MarketActivity] = None


def get_market_activity() -> MarketActivity:
    global _activity
    if _activity is None:
        _activity = MarketActivity()
    return _activity
