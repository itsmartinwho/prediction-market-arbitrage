"""The scan: the one implementation behind both ways the app runs.

One scan reads the N most liquid open two-outcome markets from Gamma (pages
of 100, fetched at once), their order books from the CLOB (100 tokens per
/books request, a few at once), and applies the YES + NO test to each.

- On Vercel (on_request mode) an endpoint calls `ScanService.latest()`, which
  scans only when the cached result is older than the cache TTL.
- On your own machine (continuous mode) the loop in services/scanner.py calls
  `ScanService.fresh()` every few seconds and sends the alerts.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Awaitable, Callable, List, Optional

import httpx

from app.clients.polymarket.clob_client import CLOBClient
from app.clients.polymarket.gamma_client import GammaClient
from app.clients.polymarket.http import session
from app.config import get_settings
from app.core.arbitrage import YesNoArbitrageDetector
from app.core.cache import TTLCache, shared_cache
from app.models.opportunity import Opportunity


@dataclass
class ScanResult:
    opportunities: List[Opportunity]
    diagnostics: dict
    market_limit: int
    markets_scanned: int
    started_at: datetime
    finished_at: datetime
    duration_ms: float
    threshold: float
    fee: float = YesNoArbitrageDetector.POLYMARKET_FEE

    def get(self, opp_id: str) -> Optional[Opportunity]:
        return next((o for o in self.opportunities if o.id == opp_id), None)


async def run_scan(
    market_limit: Optional[int] = None,
    threshold: Optional[float] = None,
    http: Optional[httpx.AsyncClient] = None,
) -> ScanResult:
    """Scan the `market_limit` most liquid two-outcome markets once."""
    settings = get_settings()
    limit = market_limit or settings.resolved_market_limit
    threshold = threshold if threshold is not None else settings.min_profit_threshold

    started_at = datetime.now(timezone.utc)
    clock = time.perf_counter()
    async with session(http) as client:
        gamma = GammaClient(http=client)
        clob = CLOBClient(http=client)
        detector = YesNoArbitrageDetector(gamma, clob, min_profit_threshold=threshold)
        markets = await gamma.get_top_markets(limit)
        opportunities = await detector.scan_markets(markets)

    return ScanResult(
        opportunities=opportunities,
        diagnostics=detector.get_diagnostics(),
        market_limit=limit,
        markets_scanned=len(markets),
        started_at=started_at,
        finished_at=datetime.now(timezone.utc),
        duration_ms=(time.perf_counter() - clock) * 1000,
        threshold=threshold,
    )


class ScanService:
    """Hands out scan results, scanning only when the cached one is too old."""

    KEY = "scan"

    def __init__(
        self,
        cache: Optional[TTLCache] = None,
        ttl: Optional[float] = None,
        scan: Optional[Callable[[], Awaitable[ScanResult]]] = None,
    ):
        self.cache = cache or shared_cache()
        self.ttl = ttl if ttl is not None else get_settings().cache_ttl_seconds
        self._scan = scan or run_scan
        self.scan_count = 0

    async def _counted_scan(self) -> ScanResult:
        result = await self._scan()
        self.scan_count += 1
        return result

    async def latest(self, max_age: Optional[float] = None) -> ScanResult:
        """A result no older than `max_age` seconds (default: the cache TTL).

        Pass float("inf") to take whatever the continuous loop last produced,
        waiting for its first scan if none has finished yet.
        """
        ttl = self.ttl if max_age is None else max_age
        entry = await self.cache.get(self.KEY, ttl, self._counted_scan)
        return entry.value

    async def fresh(self) -> ScanResult:
        """Scan now (or join a scan already running)."""
        entry = await self.cache.refresh(self.KEY, self._counted_scan)
        return entry.value

    def peek(self) -> Optional[ScanResult]:
        entry = self.cache.peek(self.KEY)
        return entry.value if entry else None


_service: Optional[ScanService] = None


def get_scan_service() -> ScanService:
    global _service
    if _service is None:
        _service = ScanService()
    return _service
