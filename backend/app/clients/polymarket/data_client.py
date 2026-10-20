"""Polymarket Data API client for trades and activity."""
from __future__ import annotations
import logging
from typing import Any, Optional, List
from datetime import datetime, timezone
import httpx
from pydantic import BaseModel

from .http import get_json, new_client

logger = logging.getLogger(__name__)

# Data API base URL
DATA_API_URL = "https://data-api.polymarket.com"


class Trade(BaseModel):
    """A trade from Polymarket."""
    proxy_wallet: Optional[str] = None
    side: str  # BUY or SELL
    asset: Optional[str] = None
    condition_id: str
    size: float
    price: float
    timestamp: datetime
    title: str
    slug: str
    event_slug: Optional[str] = None
    outcome: str
    outcome_index: int
    name: Optional[str] = None  # Trader name/pseudonym
    pseudonym: Optional[str] = None
    bio: Optional[str] = None
    profile_image: Optional[str] = None
    transaction_hash: Optional[str] = None

    @property
    def usd_value(self) -> float:
        """Calculate USD value of the trade."""
        return self.size * self.price

    @property
    def polymarket_url(self) -> str:
        """Get the Polymarket URL for this market."""
        if self.event_slug:
            return f"https://polymarket.com/event/{self.event_slug}"
        return f"https://polymarket.com/event/{self.slug}"

    @property
    def trader_display_name(self) -> str:
        """Get display name for the trader."""
        if self.pseudonym:
            return self.pseudonym
        if self.name:
            return self.name
        if self.proxy_wallet:
            return f"{self.proxy_wallet[:6]}...{self.proxy_wallet[-4:]}"
        return "Anonymous"


class DataClient:
    """
    Client for Polymarket Data API.

    Provides access to:
    - Recent trades (with filtering by size)
    - User activity
    - Market activity
    """

    def __init__(self, base_url: str = DATA_API_URL, http: Optional[httpx.AsyncClient] = None):
        self.base_url = base_url.rstrip("/")
        self._http = http
        self._owns_http = http is None

    @property
    def http(self) -> httpx.AsyncClient:
        if self._http is None or self._http.is_closed:
            self._http = new_client()
            self._owns_http = True
        return self._http

    async def close(self):
        """Close the HTTP client if this instance made it."""
        if self._owns_http and self._http is not None and not self._http.is_closed:
            await self._http.aclose()

    async def _get(self, endpoint: str, params: dict | None = None) -> Any:
        return await get_json(self.http, f"{self.base_url}{endpoint}", params)

    async def get_recent_trades(
        self,
        limit: int = 100,
        min_usd_amount: float = 0,
        market: Optional[str] = None,
        side: Optional[str] = None,
    ) -> List[Trade]:
        """
        Get recent trades from Polymarket.

        Args:
            limit: Max trades to return (max 10000)
            min_usd_amount: Filter for trades >= this USD amount
            market: Filter by market condition ID
            side: Filter by BUY or SELL

        Returns:
            List of Trade objects
        """
        params = {
            "limit": min(limit, 10000),
            "offset": 0,
            "takerOnly": "true",
        }

        # Filter by minimum USD amount
        if min_usd_amount > 0:
            params["filterType"] = "CASH"
            params["filterAmount"] = str(min_usd_amount)

        if market:
            params["market"] = market

        if side:
            params["side"] = side

        # A failed request raises, so the dashboard can say so instead of
        # showing an empty list as if nobody had traded.
        data = await self._get("/trades", params=params)
        trades = []
        for item in data if isinstance(data, list) else []:
            trade = self._parse_trade(item)
            if trade:
                trades.append(trade)
        logger.info(f"Fetched {len(trades)} trades from Data API")
        return trades

    async def get_large_trades(
        self,
        min_usd: float = 1000,
        limit: int = 50,
    ) -> List[Trade]:
        """
        Get large trades (whale activity).

        Args:
            min_usd: Minimum USD value for a trade to be considered "large"
            limit: Max trades to return

        Returns:
            List of Trade objects sorted by value
        """
        trades = await self.get_recent_trades(
            limit=limit,
            min_usd_amount=min_usd,
        )

        # Sort by USD value descending
        trades.sort(key=lambda t: t.usd_value, reverse=True)
        return trades

    async def get_trades_for_market(
        self,
        condition_id: str,
        limit: int = 100,
    ) -> List[Trade]:
        """Get recent trades for a specific market."""
        return await self.get_recent_trades(
            limit=limit,
            market=condition_id,
        )

    def _parse_trade(self, data: dict) -> Optional[Trade]:
        """Parse raw API response into Trade model."""
        try:
            # The Data API sends unix seconds; accept ISO strings too. Always UTC.
            raw_ts = data.get("timestamp")
            if isinstance(raw_ts, (int, float)):
                timestamp = datetime.fromtimestamp(raw_ts, tz=timezone.utc)
            elif isinstance(raw_ts, str) and raw_ts:
                timestamp = datetime.fromisoformat(raw_ts.replace("Z", "+00:00"))
            else:
                timestamp = datetime.now(timezone.utc)

            return Trade(
                proxy_wallet=data.get("proxyWallet"),
                side=data.get("side", "BUY"),
                asset=data.get("asset"),
                condition_id=data.get("conditionId", ""),
                size=float(data.get("size", 0)),
                price=float(data.get("price", 0)),
                timestamp=timestamp,
                title=data.get("title", ""),
                slug=data.get("slug", ""),
                event_slug=data.get("eventSlug"),
                outcome=data.get("outcome", ""),
                outcome_index=int(data.get("outcomeIndex", 0)),
                name=data.get("name"),
                pseudonym=data.get("pseudonym"),
                bio=data.get("bio"),
                profile_image=data.get("profileImage") or data.get("profileImageOptimized"),
                transaction_hash=data.get("transactionHash"),
            )
        except Exception as e:
            logger.warning(f"Failed to parse trade: {e}")
            return None
