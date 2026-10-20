"""A fake Polymarket behind httpx.MockTransport: Gamma /markets, /events and
/public-search, CLOB /books, and Data API /trades. It records every request,
so tests can check how much a scan asks for."""
from __future__ import annotations

import json
from typing import Dict, List, Optional

import httpx


def gamma_market(i: int, liquidity: float, yes_price: float = 0.5, no_price: float = 0.5) -> dict:
    return {
        "id": str(i),
        "question": f"Market {i}?",
        "slug": f"market-{i}",
        "conditionId": f"0xc{i}",
        "active": True,
        "closed": False,
        "clobTokenIds": json.dumps([f"y{i}", f"n{i}"]),
        "outcomes": json.dumps(["Yes", "No"]),
        "outcomePrices": json.dumps([str(yes_price), str(no_price)]),
        "liquidityNum": liquidity,
        "volumeNum": liquidity * 2,
        "events": [{"slug": f"event-{i}"}],
    }


class FakePolymarket:
    def __init__(self, n_markets: int = 350):
        # Gamma lists the most liquid first
        self.markets: List[dict] = [gamma_market(i, liquidity=100_000 - i) for i in range(n_markets)]
        # token id -> best ask; a token missing here has an empty book
        self.asks: Dict[str, float] = {}
        for m in self.markets:
            yes_id, no_id = json.loads(m["clobTokenIds"])
            self.asks[yes_id] = 0.51
            self.asks[no_id] = 0.50
        self.events: List[dict] = []
        self.trades: List[dict] = []
        self.fail_books_containing: Optional[str] = None  # a token id that makes its /books chunk fail
        self.requests: List[httpx.Request] = []

    # --- helpers for assertions -------------------------------------------

    def calls(self, path: str, method: Optional[str] = None) -> List[httpx.Request]:
        return [r for r in self.requests if r.url.path == path and (method is None or r.method == method)]

    def client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(transport=httpx.MockTransport(self.handle))

    # --- the fake APIs -------------------------------------------------------

    def handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        path, params = request.url.path, request.url.params

        if request.url.host == "gamma-api.polymarket.com" and path == "/markets":
            offset, limit = int(params.get("offset", 0)), int(params.get("limit", 100))
            assert limit <= 100, "Gamma pages are at most 100 rows"
            return httpx.Response(200, json=self.markets[offset:offset + limit])

        if request.url.host == "gamma-api.polymarket.com" and path == "/events":
            return httpx.Response(200, json=self.events[: int(params.get("limit", 100))])

        if request.url.host == "gamma-api.polymarket.com" and path == "/public-search":
            q = params.get("q", "").lower()
            return httpx.Response(200, json={"events": [e for e in self.events if q in e["title"].lower()]})

        if request.url.host == "clob.polymarket.com" and path == "/books" and request.method == "POST":
            ids = [row["token_id"] for row in json.loads(request.content)]
            if self.fail_books_containing in ids:
                return httpx.Response(500, json={"error": "boom"})
            books = []
            for token_id in ids:
                ask = self.asks.get(token_id)
                asks = [{"price": str(ask), "size": "100"}, {"price": "0.99", "size": "5"}] if ask else []
                books.append({"asset_id": token_id, "bids": [], "asks": asks})
            return httpx.Response(200, json=books)

        if request.url.host == "data-api.polymarket.com" and path == "/trades":
            return httpx.Response(200, json=self.trades[: int(params.get("limit", 100))])

        return httpx.Response(404, json={"error": f"no fake for {request.method} {request.url}"})
