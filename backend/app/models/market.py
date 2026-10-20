from __future__ import annotations
"""Market data models."""
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class Token(BaseModel):
    """A tradeable token (YES or NO) in a market."""

    token_id: str
    outcome: str  # "Yes" or "No"
    price: float | None = None


class OrderBookLevel(BaseModel):
    """A single price level in the order book."""

    price: float
    size: float


class OrderBook(BaseModel):
    """Order book for a token."""

    token_id: str
    bids: list[OrderBookLevel] = Field(default_factory=list)
    asks: list[OrderBookLevel] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def best_bid(self) -> float | None:
        """Get the best (highest) bid price."""
        return self.bids[0].price if self.bids else None

    @property
    def best_ask(self) -> float | None:
        """Get the best (lowest) ask price."""
        return self.asks[0].price if self.asks else None

    @property
    def midpoint(self) -> float | None:
        """Get the midpoint between best bid and ask."""
        if self.best_bid and self.best_ask:
            return (self.best_bid + self.best_ask) / 2
        return None


class Market(BaseModel):
    """A prediction market with YES/NO outcomes."""

    id: str
    question: str
    slug: str | None = None
    description: str | None = None
    condition_id: str | None = None
    end_date: datetime | None = None
    active: bool = True
    closed: bool = False

    # Tokens
    yes_token: Token | None = None
    no_token: Token | None = None

    # Market data
    volume: float | None = None
    liquidity: float | None = None

    # Prices (from gamma API)
    yes_price: float | None = None
    no_price: float | None = None

    @property
    def combined_price(self) -> float | None:
        """Get combined YES + NO price."""
        if self.yes_price is not None and self.no_price is not None:
            return self.yes_price + self.no_price
        return None

    @property
    def is_binary(self) -> bool:
        """Check if this is a binary YES/NO market."""
        return self.yes_token is not None and self.no_token is not None
