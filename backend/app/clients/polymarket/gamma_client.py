"""Polymarket Gamma API client: markets, events and search (public, read-only)."""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, List, Optional

import httpx
from pydantic import BaseModel

from app.config import get_settings
from app.models.market import Market, Token

from .http import get_json, new_client

logger = logging.getLogger(__name__)

PAGE_SIZE = 100  # Gamma returns at most 100 rows per request


class Event(BaseModel):
    """A Polymarket event (container for one or more markets)."""
    id: str
    title: str
    slug: str
    description: Optional[str] = None
    volume: float = 0.0
    volume_24h: float = 0.0
    liquidity: float = 0.0
    end_date: Optional[datetime] = None
    market_count: int = 0
    # The first market's prices, which is the whole story for a one-market event
    yes_price: Optional[float] = None
    no_price: Optional[float] = None
    polymarket_url: str = ""


def _json_list(raw: Any) -> list:
    """Gamma sends some arrays as JSON strings ("[\"Yes\", \"No\"]")."""
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except ValueError:
            return []
    return raw if isinstance(raw, list) else []


def _float(raw: Any) -> Optional[float]:
    try:
        return float(raw) if raw not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _date(raw: Any) -> Optional[datetime]:
    if not raw or not isinstance(raw, str):
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def parse_market(data: dict, event_slug: Optional[str] = None) -> Optional[Market]:
    """A Gamma market as a Market, or None when it is closed or not two-outcome."""
    try:
        if data.get("closed", False):
            return None
        token_ids = _json_list(data.get("clobTokenIds"))
        prices = [_float(p) for p in _json_list(data.get("outcomePrices"))]
        if len(token_ids) < 2 or len(prices) < 2:
            return None

        if event_slug is None:
            events = data.get("events") or []
            event_slug = (events[0].get("slug") if events else None) or data.get("slug", "")

        yes_price, no_price = prices[0], prices[1]
        return Market(
            id=str(data.get("id", "")),
            question=data.get("question", ""),
            slug=event_slug,  # the event slug is what a polymarket.com URL needs
            description=data.get("description"),
            condition_id=data.get("conditionId"),
            end_date=data.get("endDate"),
            active=data.get("active", True),
            closed=data.get("closed", False),
            yes_token=Token(token_id=str(token_ids[0]), outcome="Yes", price=yes_price),
            no_token=Token(token_id=str(token_ids[1]), outcome="No", price=no_price),
            yes_price=yes_price,
            no_price=no_price,
            volume=_float(data.get("volumeNum", data.get("volume"))) or 0.0,
            liquidity=_float(data.get("liquidityNum", data.get("liquidity"))) or 0.0,
        )
    except Exception as e:  # one malformed row should not sink a scan
        logger.warning(f"Failed to parse market {data.get('id', 'unknown')}: {e}")
        return None


def parse_event(data: dict) -> Optional[Event]:
    try:
        slug = data.get("slug", "") or ""
        markets = data.get("markets") or []
        yes_price = no_price = None
        if markets:
            prices = [_float(p) for p in _json_list(markets[0].get("outcomePrices"))]
            if len(prices) >= 2:
                yes_price, no_price = prices[0], prices[1]
        return Event(
            id=str(data.get("id", "")),
            title=data.get("title") or slug.replace("-", " ").title(),
            slug=slug,
            description=data.get("description"),
            volume=_float(data.get("volume")) or 0.0,
            volume_24h=_float(data.get("volume24hr")) or 0.0,
            liquidity=_float(data.get("liquidity")) or 0.0,
            end_date=_date(data.get("endDate")),
            market_count=len(markets),
            yes_price=yes_price,
            no_price=no_price,
            polymarket_url=f"https://polymarket.com/event/{slug}" if slug else "",
        )
    except Exception as e:
        logger.warning(f"Failed to parse event {data.get('id', 'unknown')}: {e}")
        return None


class GammaClient:
    """
    Client for Polymarket's Gamma API: market metadata, listed prices and volume.

    No authentication. Pass `http` to share one connection pool across calls.
    API docs: https://docs.polymarket.com/developers/gamma-markets-api
    """

    def __init__(self, base_url: Optional[str] = None, http: Optional[httpx.AsyncClient] = None):
        self.base_url = (base_url or get_settings().gamma_api_url).rstrip("/")
        self._http = http
        self._owns_http = http is None

    @property
    def http(self) -> httpx.AsyncClient:
        if self._http is None or self._http.is_closed:
            self._http = new_client()
            self._owns_http = True
        return self._http

    async def close(self):
        if self._owns_http and self._http is not None and not self._http.is_closed:
            await self._http.aclose()

    async def _get(self, path: str, params: Optional[dict] = None) -> Any:
        return await get_json(self.http, f"{self.base_url}{path}", params)

    # Markets -----------------------------------------------------------------

    async def get_top_markets(self, limit: int) -> List[Market]:
        """The `limit` most liquid open two-outcome markets, most liquid first.

        Fetched as concurrent pages of 100. This is the bounded set a scan reads.
        """
        limit = max(1, limit)
        offsets = range(0, limit, PAGE_SIZE)

        async def page(offset: int) -> list:
            rows = await self._get(
                "/markets",
                {
                    "active": "true",
                    "closed": "false",
                    "order": "liquidityNum",
                    "ascending": "false",
                    "limit": min(PAGE_SIZE, limit - offset),
                    "offset": offset,
                },
            )
            return rows if isinstance(rows, list) else []

        pages = await asyncio.gather(*(page(o) for o in offsets))
        markets: List[Market] = []
        seen: set = set()
        for rows in pages:
            for row in rows:
                market = parse_market(row)
                if market and market.is_binary and market.id not in seen:
                    seen.add(market.id)
                    markets.append(market)
        markets.sort(key=lambda m: m.liquidity or 0, reverse=True)
        return markets[:limit]

    async def get_markets(self, limit: int = 50, offset: int = 0) -> List[Market]:
        """One page of open markets, most liquid first."""
        rows = await self._get(
            "/markets",
            {
                "active": "true",
                "closed": "false",
                "order": "liquidityNum",
                "ascending": "false",
                "limit": min(PAGE_SIZE, limit),
                "offset": offset,
            },
        )
        return [m for m in (parse_market(r) for r in rows or []) if m]

    async def get_market_by_id(self, market_id: str) -> Optional[Market]:
        try:
            data = await self._get(f"/markets/{market_id}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (404, 422):
                return None
            raise
        return parse_market(data) if isinstance(data, dict) else None

    # Events ------------------------------------------------------------------

    async def get_events(
        self,
        limit: int = 100,
        order: str = "volume24hr",
        end_date_min: Optional[datetime] = None,
        end_date_max: Optional[datetime] = None,
    ) -> List[Event]:
        """Open events, ordered by `order` (descending), one page of up to 100."""
        params: dict = {
            "active": "true",
            "closed": "false",
            "order": order,
            "ascending": "false",
            "limit": min(PAGE_SIZE, limit),
        }
        if end_date_min:
            params["end_date_min"] = end_date_min.isoformat()
        if end_date_max:
            params["end_date_max"] = end_date_max.isoformat()
        rows = await self._get("/events", params)
        return [e for e in (parse_event(r) for r in rows or []) if e]

    async def search_events(self, query: str, limit: int = 20) -> List[Event]:
        """Open events matching `query`, using Gamma's own search."""
        data = await self._get(
            "/public-search",
            {"q": query, "events_status": "active", "limit_per_type": min(50, limit)},
        )
        rows = (data or {}).get("events") or []
        events = [e for e in (parse_event(r) for r in rows if not r.get("closed")) if e]
        return events[:limit]
