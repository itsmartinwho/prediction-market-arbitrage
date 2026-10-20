from __future__ import annotations
"""The continuous scanner: local mode only.

Scans every few seconds through the same ScanService the request-driven
endpoints use, and alerts once per opportunity (a new combined cost is a new
opportunity). Vercel Functions keep no background work, so on Vercel this
loop does not start and nothing alerts; see README.
"""
import asyncio
import logging
from datetime import datetime
from typing import Awaitable, Callable, Optional

from app.config import get_settings
from app.core.scan import ScanService, get_scan_service
from app.models.opportunity import Opportunity

logger = logging.getLogger(__name__)


class OpportunityScanner:
    def __init__(
        self,
        service: Optional[ScanService] = None,
        on_opportunity: Optional[Callable[[Opportunity], Awaitable[None]]] = None,
        scan_interval: Optional[int] = None,
    ):
        self.service = service or get_scan_service()
        self.on_opportunity = on_opportunity
        self.scan_interval = scan_interval or get_settings().scan_interval_seconds
        self.running = False
        self._seen: set = set()
        self._scan_count = 0
        self._last_scan: Optional[datetime] = None
        self._active = 0

    @property
    def is_running(self) -> bool:
        return self.running

    @property
    def stats(self) -> dict:
        return {
            "running": self.running,
            "scan_count": self._scan_count,
            "last_scan": self._last_scan.isoformat() if self._last_scan else None,
            "active_opportunities": self._active,
            "total_seen": len(self._seen),
        }

    async def start(self):
        logger.info(f"Continuous scanner started (pause between scans: {self.scan_interval}s)")
        self.running = True
        while self.running:
            try:
                await self.scan_once()
            except Exception as e:
                logger.error(f"Scan failed: {e}", exc_info=True)
            await asyncio.sleep(self.scan_interval)

    async def stop(self):
        self.running = False

    async def scan_once(self) -> list:
        result = await self.service.fresh()
        self._scan_count += 1
        self._last_scan = result.finished_at
        self._active = len(result.opportunities)
        for opp in result.opportunities:
            if opp.id in self._seen:
                continue
            self._seen.add(opp.id)
            logger.info(f"New opportunity: {opp.market_question[:50]}")
            if self.on_opportunity:
                try:
                    await self.on_opportunity(opp)
                except Exception as e:
                    logger.error(f"Alert failed: {e}")
        logger.info(
            f"Scan #{self._scan_count}: {result.markets_scanned} markets, "
            f"{len(result.opportunities)} opportunities, {result.duration_ms / 1000:.1f}s"
        )
        return result.opportunities


_scanner: Optional[OpportunityScanner] = None


def get_scanner() -> Optional[OpportunityScanner]:
    """The running continuous scanner, or None in on_request mode."""
    return _scanner


def set_scanner(scanner: Optional[OpportunityScanner]) -> None:
    global _scanner
    _scanner = scanner
