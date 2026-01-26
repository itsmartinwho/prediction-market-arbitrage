from __future__ import annotations
"""Polymarket Gamma API client for market metadata."""
import json
import logging
from typing import Any, Optional, List
from datetime import datetime
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from pydantic import BaseModel

from app.config import get_settings
from app.models.market import Market, Token

logger = logging.getLogger(__name__)


class Event(BaseModel):
    """A Polymarket event (container for one or more markets)."""
    id: str
    title: str
    slug: str
    description: Optional[str] = None
    volume: float = 0.0
    liquidity: float = 0.0
    end_date: Optional[datetime] = None
    market_count: int = 0
    # For single-market events, include price info
    yes_price: Optional[float] = None
    no_price: Optional[float] = None
    polymarket_url: str = ""


class GammaClient:
    """
    Client for Polymarket Gamma API.

    Gamma API provides market metadata, prices, and volumes.
    No authentication required for read operations.

    API Docs: https://docs.polymarket.com/developers/gamma-markets-api
    """

    def __init__(self, base_url: str | None = None):
        settings = get_settings()
        self.base_url = base_url or settings.gamma_api_url
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=30.0,
                headers={"Accept": "application/json"},
            )
        return self._client

    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def _get(self, endpoint: str, params: dict | None = None) -> Any:
        """Make GET request with retry logic."""
        client = await self._get_client()
        response = await client.get(endpoint, params=params)
        response.raise_for_status()
        return response.json()

    async def get_events_raw(
        self,
        limit: int = 100,
        offset: int = 0,
        active: bool = True,
        closed: bool = False,
    ) -> List[dict]:
        """
        Fetch raw events from Gamma API.
        """
        params = {
            "limit": min(limit, 100),
            "offset": offset,
            "active": str(active).lower(),
            "closed": str(closed).lower(),
        }

        return await self._get("/events", params=params)

    async def get_events(
        self,
        limit: int = 100,
        offset: int = 0,
        active: bool = True,
    ) -> List[Event]:
        """
        Fetch events from Gamma API as Event objects.

        Events are the proper display unit for Polymarket.
        Each event may contain one or more markets (outcomes).
        """
        raw_events = await self.get_events_raw(limit=limit, offset=offset, active=active)
        events = []

        for raw in raw_events:
            event = self._parse_event(raw)
            if event:
                events.append(event)

        logger.info(f"Fetched {len(events)} events from Gamma API")
        return events

    def _parse_event(self, data: dict) -> Event | None:
        """Parse raw event data into Event model."""
        try:
            slug = data.get("slug", "")
            markets = data.get("markets", [])

            # Get first market's price for display (most relevant for single-market events)
            yes_price = None
            no_price = None
            if markets:
                first_market = markets[0]
                outcome_prices_raw = first_market.get("outcomePrices", "[]")
                if isinstance(outcome_prices_raw, str):
                    outcome_prices = json.loads(outcome_prices_raw)
                else:
                    outcome_prices = outcome_prices_raw or []

                if len(outcome_prices) >= 2:
                    try:
                        yes_price = float(outcome_prices[0]) if outcome_prices[0] else None
                        no_price = float(outcome_prices[1]) if outcome_prices[1] else None
                    except (ValueError, TypeError):
                        pass

            # Parse end date
            end_date = None
            end_date_str = data.get("endDate")
            if end_date_str:
                try:
                    end_date = datetime.fromisoformat(end_date_str.replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    pass

            return Event(
                id=str(data.get("id", "")),
                title=data.get("title") or slug.replace("-", " ").title(),
                slug=slug,
                description=data.get("description"),
                volume=float(data.get("volume", 0) or 0),
                liquidity=float(data.get("liquidity", 0) or 0),
                end_date=end_date,
                market_count=len(markets),
                yes_price=yes_price,
                no_price=no_price,
                polymarket_url=f"https://polymarket.com/event/{slug}" if slug else "",
            )
        except Exception as e:
            logger.warning(f"Failed to parse event {data.get('id', 'unknown')}: {e}")
            return None

    async def get_all_active_events(self, max_events: int = 300) -> List[Event]:
        """
        Fetch all active events with pagination.

        Returns events sorted by volume (highest first).
        """
        all_events = []
        offset = 0
        limit = 100

        while True:
            events = await self.get_events(limit=limit, offset=offset, active=True)
            all_events.extend(events)

            if len(events) < limit:
                break

            offset += limit

            # Safety limit
            if len(all_events) >= max_events:
                break

        # Sort by volume descending
        all_events.sort(key=lambda e: e.volume or 0, reverse=True)
        return all_events[:max_events]

    # Legacy methods for backward compatibility with arbitrage scanner
    async def get_markets_from_events(
        self,
        limit: int = 100,
        offset: int = 0,
        active: bool = True,
    ) -> List[Market]:
        """
        Fetch markets via the Events API (for arbitrage scanner).

        Note: This returns individual markets, not events.
        For display purposes, use get_events() instead.
        """
        raw_events = await self.get_events_raw(limit=limit, offset=offset, active=active)
        markets = []

        for event in raw_events:
            event_slug = event.get("slug", "")
            event_markets = event.get("markets", [])

            for market_data in event_markets:
                market = self._parse_market_from_event(market_data, event_slug)
                if market and market.is_binary:
                    markets.append(market)

        logger.info(f"Fetched {len(markets)} binary markets from {len(raw_events)} events")
        return markets

    def _parse_market_from_event(self, data: dict, event_slug: str) -> Market | None:
        """Parse market from event data, preserving event_slug for URLs."""
        try:
            # Skip closed markets
            if data.get("closed", False):
                return None

            # Extract token IDs - may be JSON string or list
            clob_token_ids_raw = data.get("clobTokenIds", "[]")
            if isinstance(clob_token_ids_raw, str):
                clob_token_ids = json.loads(clob_token_ids_raw)
            else:
                clob_token_ids = clob_token_ids_raw or []

            # Extract prices - may be JSON string or list
            outcome_prices_raw = data.get("outcomePrices", "[]")
            if isinstance(outcome_prices_raw, str):
                outcome_prices = json.loads(outcome_prices_raw)
            else:
                outcome_prices = outcome_prices_raw or []

            # Parse prices to floats
            prices = []
            for p in outcome_prices:
                try:
                    prices.append(float(p) if p else None)
                except (ValueError, TypeError):
                    prices.append(None)

            # Need at least 2 token IDs and prices for binary market
            if len(clob_token_ids) < 2 or len(prices) < 2:
                return None

            yes_price = prices[0]
            no_price = prices[1]

            yes_token = Token(
                token_id=str(clob_token_ids[0]),
                outcome="Yes",
                price=yes_price
            )
            no_token = Token(
                token_id=str(clob_token_ids[1]),
                outcome="No",
                price=no_price
            )

            # Use event_slug for the market - this is what we need for URLs!
            return Market(
                id=str(data.get("id", "")),
                question=data.get("question", ""),
                slug=event_slug,  # Use event_slug, not market slug!
                description=data.get("description"),
                condition_id=data.get("conditionId"),
                end_date=data.get("endDate"),
                active=data.get("active", True),
                closed=data.get("closed", False),
                yes_token=yes_token,
                no_token=no_token,
                yes_price=yes_price,
                no_price=no_price,
                volume=float(data.get("volume", 0) or 0),
                liquidity=float(data.get("liquidity", 0) or 0),
            )
        except Exception as e:
            logger.warning(f"Failed to parse market {data.get('id', 'unknown')}: {e}")
            return None

    async def get_all_active_markets(self) -> list[Market]:
        """
        Fetch all active binary markets using Events API.

        This method is used by the arbitrage scanner.
        For display purposes, use get_all_active_events() instead.
        """
        all_markets = []
        offset = 0
        limit = 100

        while True:
            markets = await self.get_markets_from_events(limit=limit, offset=offset, active=True)
            all_markets.extend(markets)

            if len(markets) < limit:
                break

            offset += limit

            # Safety limit - don't fetch more than 500 events worth
            if offset >= 500:
                break

        # Sort by volume descending
        all_markets.sort(key=lambda m: m.volume or 0, reverse=True)
        return all_markets

    # Legacy methods
    async def get_markets(
        self,
        limit: int = 100,
        offset: int = 0,
        active: bool = True,
        closed: bool = False,
    ) -> list[Market]:
        """Legacy endpoint - use get_markets_from_events() instead."""
        return await self.get_markets_from_events(limit=limit, offset=offset, active=active)

    async def get_market_by_id(self, market_id: str) -> Market | None:
        """Fetch a single market by ID."""
        try:
            data = await self._get(f"/markets/{market_id}")
            return self._parse_market_from_event(data, data.get("slug", ""))
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise
