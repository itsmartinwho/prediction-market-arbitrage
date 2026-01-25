from __future__ import annotations
"""Polymarket Gamma API client for market metadata."""
import json
import logging
from typing import Any
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.models.market import Market, Token

logger = logging.getLogger(__name__)


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

    async def get_markets(
        self,
        limit: int = 100,
        offset: int = 0,
        active: bool = True,
        closed: bool = False,
    ) -> list[Market]:
        """
        Fetch markets from Gamma API.

        Args:
            limit: Max number of markets to return (max 100)
            offset: Pagination offset
            active: Filter for active markets
            closed: Filter for closed markets

        Returns:
            List of Market objects
        """
        params = {
            "limit": min(limit, 100),
            "offset": offset,
            "active": str(active).lower(),
            "closed": str(closed).lower(),
        }

        data = await self._get("/markets", params=params)
        markets = []

        for item in data:
            market = self._parse_market(item)
            if market and market.is_binary:
                markets.append(market)

        logger.info(f"Fetched {len(markets)} binary markets from Gamma API")
        return markets

    async def get_market_by_id(self, market_id: str) -> Market | None:
        """Fetch a single market by ID."""
        try:
            data = await self._get(f"/markets/{market_id}")
            return self._parse_market(data)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    async def get_market_by_condition_id(self, condition_id: str) -> Market | None:
        """Fetch a market by condition ID."""
        params = {"condition_id": condition_id}
        data = await self._get("/markets", params=params)
        if data:
            return self._parse_market(data[0])
        return None

    def _parse_market(self, data: dict) -> Market | None:
        """Parse raw API response into Market model."""
        try:
            # Skip closed markets for arbitrage
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

            return Market(
                id=str(data.get("id", "")),
                question=data.get("question", ""),
                slug=data.get("slug"),
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
        """Fetch all active binary markets with pagination."""
        all_markets = []
        offset = 0
        limit = 100

        while True:
            markets = await self.get_markets(limit=limit, offset=offset, active=True)
            all_markets.extend(markets)

            if len(markets) < limit:
                break

            offset += limit

        return all_markets
