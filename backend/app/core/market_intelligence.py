"""Market intelligence - derives trading signals from real Polymarket activity."""
from __future__ import annotations
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel

from app.clients.polymarket.gamma_client import GammaClient
from app.clients.polymarket.http import session
from app.config import get_settings
from app.core.cache import TTLCache, shared_cache
from app.core.whale_tracker import recent_large_trades
from app.models.market import Market

SIGNAL_MARKETS = 200  # the most liquid markets the price and volume signals look at

logger = logging.getLogger(__name__)


class MarketSignal(BaseModel):
    """A trading signal derived from market activity."""

    id: str
    type: str  # "whale_trade", "price_spike", "volume_surge"
    title: str
    summary: str
    market_question: str
    market_url: str
    signal: str  # "BUY_YES", "BUY_NO", "SELL_YES", "SELL_NO", "WATCH"
    confidence: float  # 0-1
    current_price: Optional[float] = None
    reasoning: str
    detected_at: datetime
    source_data: dict = {}


class MarketIntelligence:
    """
    Derives trading signals from real Polymarket activity.

    Every signal is computed from live Polymarket data; nothing is mocked.
    They are heuristics for research, not recommendations.

    Signal types:
    - whale_trade: Large trades indicating informed positioning
    - price_spike: Markets with extreme prices showing strong conviction
    - volume_surge: High activity markets worth watching
    """

    def __init__(self, cache: Optional[TTLCache] = None, http=None):
        self.cache = cache or shared_cache()
        self._http = http
        self._recent_signals: List[MarketSignal] = []

    async def _top_markets(self) -> List[Market]:
        """The most liquid open markets, cached like every other list."""

        async def compute():
            async with session(self._http) as client:
                return await GammaClient(http=client).get_top_markets(SIGNAL_MARKETS)

        entry = await self.cache.get(f"markets:top:{SIGNAL_MARKETS}", get_settings().cache_ttl_seconds, compute)
        return entry.value

    async def get_signals(self, limit: int = 20) -> List[MarketSignal]:
        """
        Get recent trading signals from market activity.

        Combines signals from whale trades, price movements, and volume.
        """
        # The three sources run at once. One failing leaves the other two;
        # all three failing is an error, not an empty list.
        results = await asyncio.gather(
            self._get_whale_signals(limit=12),
            self._get_price_signals(limit=5),
            self._get_volume_signals(limit=5),
            return_exceptions=True,
        )
        failures = [r for r in results if isinstance(r, BaseException)]
        for failure in failures:
            logger.warning(f"A signal source failed: {failure}")
        if len(failures) == len(results):
            raise failures[0]
        signals = [s for r in results if not isinstance(r, BaseException) for s in r]

        # Sort by confidence and recency
        signals.sort(key=lambda s: (s.confidence, s.detected_at), reverse=True)
        self._recent_signals = signals[:limit]
        return self._recent_signals

    async def _get_whale_signals(self, limit: int = 10) -> List[MarketSignal]:
        """Generate signals from large trades (>$5K)."""
        trades = await recent_large_trades(5000, limit * 2, cache=self.cache, http=self._http)
        trades = sorted(trades, key=lambda t: t.usd_value, reverse=True)
        signals = []

        seen_markets = set()  # Avoid duplicate signals for same market

        for trade in trades:
            # Skip if we already have a signal for this market
            market_key = f"{trade.title}-{trade.outcome}"
            if market_key in seen_markets:
                continue
            seen_markets.add(market_key)

            # Determine signal based on trade direction
            if trade.side == "BUY":
                signal = f"BUY_{trade.outcome.upper()}"
                action_text = "bought"
            else:
                signal = f"SELL_{trade.outcome.upper()}"
                action_text = "sold"

            # Higher USD = higher confidence
            confidence = min(0.9, 0.5 + (trade.usd_value / 50000))

            signals.append(
                MarketSignal(
                    id=f"whale-{trade.transaction_hash or datetime.now(timezone.utc).isoformat()}",
                    type="whale_trade",
                    title=f"${trade.usd_value:,.0f} {trade.side} {trade.outcome}",
                    summary=f"{trade.trader_display_name} {action_text} ${trade.usd_value:,.0f} of {trade.outcome} @ {trade.price:.2f}",
                    market_question=trade.title,
                    market_url=trade.polymarket_url,  # Data API has event_slug
                    signal=signal,
                    confidence=confidence,
                    current_price=trade.price,
                    reasoning=f"Large trade signals informed positioning. Whale betting {trade.outcome} at {trade.price*100:.0f}%.",
                    detected_at=trade.timestamp,
                    source_data={
                        "trader": trade.trader_display_name,
                        "usd_value": trade.usd_value,
                        "side": trade.side,
                    },
                )
            )

            if len(signals) >= limit:
                break

        return signals


    async def _get_price_signals(self, limit: int = 5) -> List[MarketSignal]:
        """Generate signals from markets with extreme prices."""
        markets = await self._top_markets()

        # Find markets with extreme prices (>90% or <10%)
        extreme_markets = [
            m
            for m in markets
            if m.yes_price and (m.yes_price > 0.90 or m.yes_price < 0.10)
        ]

        # Sort by how extreme (closest to 0 or 1)
        extreme_markets.sort(
            key=lambda m: min(m.yes_price or 0.5, 1 - (m.yes_price or 0.5)),
        )

        signals = []
        for market in extreme_markets[:limit]:
            is_high = (market.yes_price or 0) > 0.5
            price_pct = (market.yes_price or 0) * 100

            # market.slug now contains event_slug from Events API
            url = f"https://polymarket.com/event/{market.slug}" if market.slug else ""

            signals.append(
                MarketSignal(
                    id=f"price-{market.id}",
                    type="price_spike",
                    title=f"{'YES' if is_high else 'NO'} at {price_pct:.0f}%",
                    summary=f"Market showing extreme conviction. {'YES' if is_high else 'NO'} trading at {price_pct:.1f}%.",
                    market_question=market.question,
                    market_url=url,
                    signal="WATCH",  # Extreme prices are risky to fade
                    confidence=0.4,  # Lower confidence for contrarian plays
                    current_price=market.yes_price,
                    reasoning=f"Strong market consensus at {price_pct:.0f}%. Research before trading against momentum.",
                    detected_at=datetime.now(timezone.utc),
                    source_data={
                        "yes_price": market.yes_price,
                        "volume": market.volume,
                    },
                )
            )

        return signals


    async def _get_volume_signals(self, limit: int = 5) -> List[MarketSignal]:
        """Generate signals from high-volume markets."""
        markets = sorted(await self._top_markets(), key=lambda m: m.volume or 0, reverse=True)

        signals = []
        for market in markets[:limit * 2]:
            volume = market.volume or 0
            if volume < 100000:  # Skip low volume markets
                continue

            # market.slug now contains event_slug from Events API
            url = f"https://polymarket.com/event/{market.slug}" if market.slug else ""

            # Format volume
            if volume >= 1_000_000:
                vol_str = f"${volume / 1_000_000:.1f}M"
            else:
                vol_str = f"${volume / 1_000:.0f}K"

            signals.append(
                MarketSignal(
                    id=f"volume-{market.id}",
                    type="volume_surge",
                    title=f"High Activity: {vol_str} volume",
                    summary=f"Market seeing significant trading activity with {vol_str} total volume.",
                    market_question=market.question,
                    market_url=url,
                    signal="WATCH",
                    confidence=0.5,
                    current_price=market.yes_price,
                    reasoning="High volume indicates strong market interest. Good liquidity for entry/exit.",
                    detected_at=datetime.now(timezone.utc),
                    source_data={
                        "volume": market.volume,
                        "liquidity": market.liquidity,
                    },
                )
            )

            if len(signals) >= limit:
                break

        return signals



# Global singleton instance
_intelligence_instance: Optional[MarketIntelligence] = None


def get_market_intelligence() -> MarketIntelligence:
    """Get the global MarketIntelligence singleton."""
    global _intelligence_instance
    if _intelligence_instance is None:
        _intelligence_instance = MarketIntelligence()
    return _intelligence_instance
