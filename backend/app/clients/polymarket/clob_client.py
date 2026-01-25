from __future__ import annotations
"""Polymarket CLOB API client for order books and trading."""
import logging
from typing import Any
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.models.market import OrderBook, OrderBookLevel

logger = logging.getLogger(__name__)


class CLOBClient:
    """
    Client for Polymarket CLOB (Central Limit Order Book) API.

    CLOB API provides order book data and trading functionality.
    - Public endpoints (order books, prices) require no auth
    - Trading endpoints require L2 API credentials

    API Docs: https://docs.polymarket.com/developers/CLOB
    """

    def __init__(self, base_url: str | None = None):
        settings = get_settings()
        self.base_url = base_url or settings.clob_api_url
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

    async def get_order_book(self, token_id: str) -> OrderBook:
        """
        Get the order book for a token.

        Args:
            token_id: The CLOB token ID (YES or NO token)

        Returns:
            OrderBook with bids and asks
        """
        data = await self._get("/book", params={"token_id": token_id})

        bids = [
            OrderBookLevel(price=float(level["price"]), size=float(level["size"]))
            for level in data.get("bids", [])
        ]
        asks = [
            OrderBookLevel(price=float(level["price"]), size=float(level["size"]))
            for level in data.get("asks", [])
        ]

        # Sort: bids descending (highest first), asks ascending (lowest first)
        bids.sort(key=lambda x: x.price, reverse=True)
        asks.sort(key=lambda x: x.price)

        return OrderBook(token_id=token_id, bids=bids, asks=asks)

    async def get_midpoint(self, token_id: str) -> float | None:
        """
        Get the midpoint price for a token.

        Args:
            token_id: The CLOB token ID

        Returns:
            Midpoint price or None if no liquidity
        """
        try:
            data = await self._get("/midpoint", params={"token_id": token_id})
            return float(data.get("mid", 0))
        except Exception:
            return None

    async def get_price(self, token_id: str, side: str = "buy") -> float | None:
        """
        Get the best price for a token.

        Args:
            token_id: The CLOB token ID
            side: "buy" (best ask) or "sell" (best bid)

        Returns:
            Best price or None if no liquidity
        """
        try:
            data = await self._get(
                "/price", params={"token_id": token_id, "side": side}
            )
            return float(data.get("price", 0))
        except Exception:
            return None

    async def get_spread(self, token_id: str) -> dict | None:
        """
        Get the bid-ask spread for a token.

        Returns:
            Dict with bid, ask, and spread
        """
        try:
            data = await self._get("/spread", params={"token_id": token_id})
            return {
                "bid": float(data.get("bid", 0)),
                "ask": float(data.get("ask", 0)),
                "spread": float(data.get("spread", 0)),
            }
        except Exception:
            return None

    async def get_best_ask(self, token_id: str) -> float | None:
        """
        Get the best (lowest) ask price - what you'd pay to buy.

        This is the key price for arbitrage detection.
        """
        book = await self.get_order_book(token_id)
        return book.best_ask

    async def get_best_bid(self, token_id: str) -> float | None:
        """
        Get the best (highest) bid price - what you'd receive to sell.
        """
        book = await self.get_order_book(token_id)
        return book.best_bid

    async def get_order_books_batch(
        self, token_ids: list[str]
    ) -> dict[str, OrderBook]:
        """
        Get order books for multiple tokens.

        Note: Makes parallel requests, be mindful of rate limits.
        """
        import asyncio

        async def fetch_book(token_id: str) -> tuple[str, OrderBook | None]:
            try:
                book = await self.get_order_book(token_id)
                return token_id, book
            except Exception as e:
                logger.warning(f"Failed to fetch order book for {token_id}: {e}")
                return token_id, None

        results = await asyncio.gather(*[fetch_book(tid) for tid in token_ids])
        return {tid: book for tid, book in results if book is not None}


# Placeholder for future auto-execution
class CLOBTradingClient(CLOBClient):
    """
    Extended CLOB client with trading capabilities.

    NOT IMPLEMENTED YET - scaffolded for future auto-execution feature.

    To enable:
    1. Set ENABLE_AUTO_EXECUTE=true
    2. Configure POLYMARKET_PRIVATE_KEY
    3. Ensure wallet has USDC on Polygon
    4. Set allowances for Polymarket contracts
    """

    def __init__(self, private_key: str | None = None, **kwargs):
        super().__init__(**kwargs)
        self.private_key = private_key
        self._trading_enabled = False

    async def create_order(
        self,
        token_id: str,
        side: str,  # "BUY" or "SELL"
        size: float,
        price: float,
    ) -> dict:
        """
        Place a limit order.

        NOT IMPLEMENTED - placeholder for future auto-execution.
        """
        raise NotImplementedError(
            "Auto-execution is not enabled. "
            "Set ENABLE_AUTO_EXECUTE=true to enable trading."
        )

    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order. NOT IMPLEMENTED."""
        raise NotImplementedError("Auto-execution is not enabled.")

    async def get_open_orders(self) -> list[dict]:
        """Get open orders. NOT IMPLEMENTED."""
        raise NotImplementedError("Auto-execution is not enabled.")
