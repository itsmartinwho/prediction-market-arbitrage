"""Polymarket CLOB API client: public, read-only order book data."""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

import httpx

from app.config import get_settings
from app.models.market import OrderBook, OrderBookLevel

from .http import get_json, new_client, post_json

logger = logging.getLogger(__name__)

BOOKS_CHUNK = 100  # token ids per /books request
BOOKS_CONCURRENCY = 4  # /books requests in flight at once


def parse_book(data: dict, token_id: Optional[str] = None) -> OrderBook:
    """An order book with bids highest first and asks lowest first."""

    def levels(rows: Any) -> List[OrderBookLevel]:
        out = []
        for row in rows or []:
            try:
                out.append(OrderBookLevel(price=float(row["price"]), size=float(row["size"])))
            except (KeyError, TypeError, ValueError):
                continue
        return out

    bids = sorted(levels(data.get("bids")), key=lambda x: x.price, reverse=True)
    asks = sorted(levels(data.get("asks")), key=lambda x: x.price)
    return OrderBook(token_id=str(token_id or data.get("asset_id", "")), bids=bids, asks=asks)


@dataclass
class BookBatch:
    """Order books by token id, and the ids whose request failed."""

    books: Dict[str, OrderBook] = field(default_factory=dict)
    failed: Set[str] = field(default_factory=set)


class CLOBClient:
    """
    Client for Polymarket's CLOB (central limit order book) API.

    Only public market-data endpoints are used. There is no authentication,
    signing or order placement anywhere in this app.

    API docs: https://docs.polymarket.com/developers/CLOB
    """

    def __init__(self, base_url: Optional[str] = None, http: Optional[httpx.AsyncClient] = None):
        self.base_url = (base_url or get_settings().clob_api_url).rstrip("/")
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

    async def get_order_book(self, token_id: str) -> OrderBook:
        """The order book for one token (GET /book)."""
        data = await get_json(self.http, f"{self.base_url}/book", {"token_id": token_id})
        return parse_book(data, token_id)

    async def get_best_ask(self, token_id: str) -> Optional[float]:
        """The lowest ask for one token: what buying it costs right now."""
        return (await self.get_order_book(token_id)).best_ask

    async def get_best_bid(self, token_id: str) -> Optional[float]:
        return (await self.get_order_book(token_id)).best_bid

    async def get_order_books(self, token_ids: List[str]) -> BookBatch:
        """Order books for many tokens, 100 per /books request, a few requests at once.

        A failed request does not fail the batch: its ids land in `failed`.
        """
        batch = BookBatch()
        unique = list(dict.fromkeys(t for t in token_ids if t))
        chunks = [unique[i:i + BOOKS_CHUNK] for i in range(0, len(unique), BOOKS_CHUNK)]
        gate = asyncio.Semaphore(BOOKS_CONCURRENCY)

        async def fetch(chunk: List[str]) -> None:
            async with gate:
                try:
                    rows = await post_json(self.http, f"{self.base_url}/books", [{"token_id": t} for t in chunk])
                except Exception as e:
                    logger.warning(f"/books failed for {len(chunk)} tokens: {e}")
                    batch.failed.update(chunk)
                    return
            for row in rows if isinstance(rows, list) else []:
                book = parse_book(row)
                if book.token_id:
                    batch.books[book.token_id] = book

        await asyncio.gather(*(fetch(c) for c in chunks))
        return batch
