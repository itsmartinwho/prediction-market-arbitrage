from __future__ import annotations
"""Background scanner service for arbitrage opportunities."""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Callable, Awaitable

from app.config import get_settings
from app.core.arbitrage import YesNoArbitrageDetector
from app.models.opportunity import Opportunity
from app.clients.polymarket import GammaClient

logger = logging.getLogger(__name__)


class OpportunityScanner:
    """
    Background service that continuously scans for arbitrage opportunities.

    Features:
    - Periodic scanning (configurable interval)
    - Deduplication (don't alert same opportunity twice)
    - Callback-based notifications
    - Graceful shutdown
    """

    def __init__(
        self,
        detector: YesNoArbitrageDetector | None = None,
        on_opportunity: Callable[[Opportunity], Awaitable[None]] | None = None,
        scan_interval: int | None = None,
    ):
        self.detector = detector or YesNoArbitrageDetector()
        self.on_opportunity = on_opportunity

        settings = get_settings()
        self.scan_interval = scan_interval or settings.scan_interval_seconds

        # State
        self.running = False
        self.opportunities: dict[str, Opportunity] = {}
        self._seen_opportunities: set[str] = set()
        self._last_scan: datetime | None = None
        self._scan_count = 0

    @property
    def is_running(self) -> bool:
        return self.running

    @property
    def stats(self) -> dict:
        """Get scanner statistics."""
        return {
            "running": self.running,
            "scan_count": self._scan_count,
            "last_scan": self._last_scan.isoformat() if self._last_scan else None,
            "active_opportunities": len(self.opportunities),
            "total_seen": len(self._seen_opportunities),
        }

    async def start(self):
        """Start the scanner loop."""
        logger.info(
            f"Starting opportunity scanner (interval: {self.scan_interval}s)"
        )
        self.running = True

        while self.running:
            try:
                await self._scan_cycle()
            except Exception as e:
                logger.error(f"Scanner error: {e}", exc_info=True)

            await asyncio.sleep(self.scan_interval)

    async def stop(self):
        """Stop the scanner gracefully."""
        logger.info("Stopping opportunity scanner...")
        self.running = False
        await self.detector.close()

    async def _scan_cycle(self):
        """Run one scan cycle."""
        start_time = datetime.utcnow()
        self._scan_count += 1

        logger.debug(f"Starting scan cycle #{self._scan_count}")

        # Get opportunities
        new_opps = await self.detector.scan_all_markets()

        # Process opportunities
        current_ids = set()
        for opp in new_opps:
            current_ids.add(opp.id)

            # Check if this is new
            if opp.id not in self._seen_opportunities:
                self._seen_opportunities.add(opp.id)
                self.opportunities[opp.id] = opp

                logger.info(f"New opportunity: {opp.market_question[:50]}...")

                # Trigger callback
                if self.on_opportunity:
                    try:
                        await self.on_opportunity(opp)
                    except Exception as e:
                        logger.error(f"Callback error: {e}")
            else:
                # Update existing opportunity
                self.opportunities[opp.id] = opp

        # Remove stale opportunities (not seen in last scan)
        stale_ids = set(self.opportunities.keys()) - current_ids
        for stale_id in stale_ids:
            del self.opportunities[stale_id]
            logger.debug(f"Removed stale opportunity: {stale_id}")

        self._last_scan = datetime.utcnow()
        duration = (self._last_scan - start_time).total_seconds()

        logger.info(
            f"Scan #{self._scan_count} complete: "
            f"{len(new_opps)} opportunities found, "
            f"{len(stale_ids)} removed, "
            f"{duration:.2f}s"
        )

    def get_opportunities(self) -> list[Opportunity]:
        """Get current opportunities sorted by edge."""
        return sorted(
            self.opportunities.values(),
            key=lambda x: x.edge_percent,
            reverse=True,
        )

    def get_opportunity(self, opp_id: str) -> Opportunity | None:
        """Get a specific opportunity by ID."""
        return self.opportunities.get(opp_id)

    async def scan_once(self) -> list[Opportunity]:
        """Run a single scan and return opportunities."""
        await self._scan_cycle()
        return self.get_opportunities()


class FastScanner:
    """
    Faster scanner using Gamma API prices only.

    Less accurate than full CLOB scanning, but much faster.
    Good for quick checks and initial filtering.
    """

    def __init__(self):
        self.gamma = GammaClient()
        self.detector = YesNoArbitrageDetector()

    async def scan(self) -> list[Opportunity]:
        """Quick scan using Gamma API prices."""
        markets = await self.gamma.get_all_active_markets()
        return await self.detector.scan_markets_fast(markets)

    async def close(self):
        await self.gamma.close()
        await self.detector.close()
