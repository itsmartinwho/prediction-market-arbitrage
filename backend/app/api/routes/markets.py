from __future__ import annotations
"""Market data endpoints."""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.clients.polymarket import GammaClient, CLOBClient
from app.models.market import Market, OrderBook

router = APIRouter(prefix="/markets", tags=["markets"])


class MarketResponse(BaseModel):
    """Market API response."""

    id: str
    question: str
    slug: str | None = None
    yes_price: float | None = None
    no_price: float | None = None
    combined_price: float | None = None
    volume: float | None = None
    liquidity: float | None = None
    active: bool = True
    yes_token_id: str | None = None
    no_token_id: str | None = None


class MarketsListResponse(BaseModel):
    """List of markets response."""

    markets: list[MarketResponse]
    count: int


@router.get("", response_model=MarketsListResponse)
async def get_markets(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0, le=10000),
):
    """
    Open two-outcome markets, most liquid first, with the prices Gamma lists.
    """
    gamma = GammaClient()
    try:
        markets = await gamma.get_markets(limit=limit, offset=offset)

        responses = []
        for market in markets:
            responses.append(
                MarketResponse(
                    id=market.id,
                    question=market.question,
                    slug=market.slug,
                    yes_price=market.yes_price,
                    no_price=market.no_price,
                    combined_price=market.combined_price,
                    volume=market.volume,
                    liquidity=market.liquidity,
                    active=market.active,
                    yes_token_id=market.yes_token.token_id if market.yes_token else None,
                    no_token_id=market.no_token.token_id if market.no_token else None,
                )
            )

        return MarketsListResponse(markets=responses, count=len(responses))
    finally:
        await gamma.close()


@router.get("/{market_id}", response_model=MarketResponse)
async def get_market(market_id: str):
    """Get a single market by ID."""
    gamma = GammaClient()
    try:
        market = await gamma.get_market_by_id(market_id)
        if not market:
            raise HTTPException(status_code=404, detail="Market not found")

        return MarketResponse(
            id=market.id,
            question=market.question,
            slug=market.slug,
            yes_price=market.yes_price,
            no_price=market.no_price,
            combined_price=market.combined_price,
            volume=market.volume,
            liquidity=market.liquidity,
            active=market.active,
            yes_token_id=market.yes_token.token_id if market.yes_token else None,
            no_token_id=market.no_token.token_id if market.no_token else None,
        )
    finally:
        await gamma.close()


class OrderBookResponse(BaseModel):
    """Order book response."""

    token_id: str
    best_bid: float | None = None
    best_ask: float | None = None
    midpoint: float | None = None
    bids: list[dict]
    asks: list[dict]


@router.get("/{market_id}/orderbook")
async def get_market_orderbook(market_id: str):
    """
    Get order books for a market's YES and NO tokens.

    Returns the full order book from CLOB API.
    """
    gamma = GammaClient()
    clob = CLOBClient()

    try:
        market = await gamma.get_market_by_id(market_id)
        if not market:
            raise HTTPException(status_code=404, detail="Market not found")

        if not market.yes_token or not market.no_token:
            raise HTTPException(status_code=400, detail="Market is not binary")

        batch = await clob.get_order_books([market.yes_token.token_id, market.no_token.token_id])
        yes_book = batch.books.get(market.yes_token.token_id)
        no_book = batch.books.get(market.no_token.token_id)
        if yes_book is None or no_book is None:
            raise HTTPException(status_code=502, detail="The CLOB did not return both order books")

        return {
            "market_id": market_id,
            "question": market.question,
            "yes": OrderBookResponse(
                token_id=yes_book.token_id,
                best_bid=yes_book.best_bid,
                best_ask=yes_book.best_ask,
                midpoint=yes_book.midpoint,
                bids=[{"price": b.price, "size": b.size} for b in yes_book.bids[:10]],
                asks=[{"price": a.price, "size": a.size} for a in yes_book.asks[:10]],
            ),
            "no": OrderBookResponse(
                token_id=no_book.token_id,
                best_bid=no_book.best_bid,
                best_ask=no_book.best_ask,
                midpoint=no_book.midpoint,
                bids=[{"price": b.price, "size": b.size} for b in no_book.bids[:10]],
                asks=[{"price": a.price, "size": a.size} for a in no_book.asks[:10]],
            ),
        }
    finally:
        await gamma.close()
        await clob.close()
