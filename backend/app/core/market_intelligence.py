"""Market intelligence - derives trading signals from real Polymarket activity."""
from __future__ import annotations
import logging
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

from app.clients.polymarket.data_client import DataClient, Trade
from app.clients.polymarket.gamma_client import GammaClient
from app.core.event_slug_cache import get_event_slug_cache

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

    This replaces the mock news tracker with actionable signals
    based on actual market data from the Polymarket Data API.

    Signal types:
    - whale_trade: Large trades indicating informed positioning
    - price_spike: Markets with extreme prices showing strong conviction
    - volume_surge: High activity markets worth watching
    """

    def __init__(self):
        self.data_client = DataClient()
        self.gamma_client = GammaClient()
        self.slug_cache = get_event_slug_cache()
        self._recent_signals: List[MarketSignal] = []

    async def get_signals(self, limit: int = 20) -> List[MarketSignal]:
        """
        Get recent trading signals from market activity.

        Combines signals from whale trades, price movements, and volume.
        """
        signals = []

        # Ensure slug cache is fresh
        if self.slug_cache.is_stale:
            await self.slug_cache.refresh_cache()

        # 1. Whale Trade Signals (most actionable)
        whale_signals = await self._get_whale_signals(limit=12)
        signals.extend(whale_signals)

        # 2. Price Movement Signals
        price_signals = await self._get_price_signals(limit=5)
        signals.extend(price_signals)

        # 3. High Volume Signals
        volume_signals = await self._get_volume_signals(limit=5)
        signals.extend(volume_signals)

        # Sort by confidence and recency
        signals.sort(key=lambda s: (s.confidence, s.detected_at), reverse=True)
        self._recent_signals = signals[:limit]
        return self._recent_signals

    async def _get_whale_signals(self, limit: int = 10) -> List[MarketSignal]:
        """Generate signals from large trades (>$5K)."""
        try:
            trades = await self.data_client.get_large_trades(min_usd=5000, limit=limit * 2)
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
                        id=f"whale-{trade.transaction_hash or datetime.utcnow().isoformat()}",
                        type="whale_trade",
                        title=f"${trade.usd_value:,.0f} {trade.side} {trade.outcome}",
                        summary=f"{trade.trader_display_name} {action_text} ${trade.usd_value:,.0f} of {trade.outcome} @ {trade.price:.2f}",
                        market_question=trade.title,
                        market_url=trade.polymarket_url,
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

        except Exception as e:
            logger.error(f"Failed to get whale signals: {e}")
            return []

    async def _get_price_signals(self, limit: int = 5) -> List[MarketSignal]:
        """Generate signals from markets with extreme prices."""
        try:
            markets = await self.gamma_client.get_all_active_markets()

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

                # Build URL using cache
                url = self.slug_cache.build_polymarket_url(
                    condition_id=market.condition_id,
                    market_slug=market.slug,
                    fallback_slug=market.slug,
                )

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
                        detected_at=datetime.utcnow(),
                        source_data={
                            "yes_price": market.yes_price,
                            "volume": market.volume,
                        },
                    )
                )

            return signals

        except Exception as e:
            logger.error(f"Failed to get price signals: {e}")
            return []

    async def _get_volume_signals(self, limit: int = 5) -> List[MarketSignal]:
        """Generate signals from high-volume markets."""
        try:
            markets = await self.gamma_client.get_all_active_markets()

            # Sort by volume descending
            markets.sort(key=lambda m: m.volume or 0, reverse=True)

            signals = []
            for market in markets[:limit]:
                volume = market.volume or 0
                if volume < 100000:  # Skip low volume markets
                    continue

                # Build URL using cache
                url = self.slug_cache.build_polymarket_url(
                    condition_id=market.condition_id,
                    market_slug=market.slug,
                    fallback_slug=market.slug,
                )

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
                        detected_at=datetime.utcnow(),
                        source_data={
                            "volume": market.volume,
                            "liquidity": market.liquidity,
                        },
                    )
                )

            return signals

        except Exception as e:
            logger.error(f"Failed to get volume signals: {e}")
            return []

    async def close(self):
        """Close the clients."""
        await self.data_client.close()
        await self.gamma_client.close()


# Global singleton instance
_intelligence_instance: Optional[MarketIntelligence] = None


def get_market_intelligence() -> MarketIntelligence:
    """Get the global MarketIntelligence singleton."""
    global _intelligence_instance
    if _intelligence_instance is None:
        _intelligence_instance = MarketIntelligence()
    return _intelligence_instance
