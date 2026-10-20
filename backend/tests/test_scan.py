"""The request-driven scan: a bounded set of markets, batched order books, and
the cache in front of it. Polymarket is faked with httpx.MockTransport."""
import asyncio
import json

import pytest

from app.core.cache import TTLCache
from app.core.scan import ScanService, run_scan
from tests.fake_polymarket import FakePolymarket


def scan_with(fake: FakePolymarket, **kwargs):
    async def go():
        async with fake.client() as http:
            return await run_scan(http=http, **kwargs)

    return asyncio.run(go())


def test_scan_reads_only_the_most_liquid_n_markets():
    fake = FakePolymarket(n_markets=350)
    result = scan_with(fake, market_limit=150)

    assert result.markets_scanned == 150
    assert result.market_limit == 150
    pages = sorted((int(r.url.params["offset"]), int(r.url.params["limit"])) for r in fake.calls("/markets"))
    assert pages == [(0, 100), (100, 50)]  # two pages, nothing past the limit
    for r in fake.calls("/markets"):
        assert r.url.params["order"] == "liquidityNum" and r.url.params["ascending"] == "false"


def test_order_books_come_in_batches_not_one_request_per_token():
    fake = FakePolymarket(n_markets=150)
    scan_with(fake, market_limit=150)

    batches = fake.calls("/books", "POST")
    sizes = sorted(len(json.loads(r.content)) for r in batches)
    assert sizes == [100, 100, 100]  # 300 tokens, 100 per request
    assert fake.calls("/book") == []  # never one book at a time


def test_scan_finds_an_edge_after_the_fee():
    fake = FakePolymarket(n_markets=20)
    fake.asks["y3"], fake.asks["n3"] = 0.48, 0.49  # 0.97 -> 0.01 net, 1.03%
    result = scan_with(fake, market_limit=20, threshold=0.01)

    assert [o.market_id for o in result.opportunities] == ["3"]
    opp = result.opportunities[0]
    assert round(opp.combined_cost, 4) == 0.97 and round(opp.edge_percent, 2) == 1.03
    assert opp.detected_at.tzinfo is not None
    assert result.diagnostics["opportunities_found"] == 1
    assert result.diagnostics["filtered_not_profitable"] == 19


def test_an_empty_book_falls_back_to_gamma_prices_and_is_counted():
    fake = FakePolymarket(n_markets=5)
    del fake.asks["n2"]  # NO side of market 2 has no asks
    result = scan_with(fake, market_limit=5)
    assert result.diagnostics["used_gamma_fallback"] == 1
    assert result.diagnostics["clob_errors"] == 0


def test_a_failed_books_request_does_not_sink_the_scan():
    fake = FakePolymarket(n_markets=100)  # 200 tokens: two /books requests
    fake.fail_books_containing = "y0"  # the first chunk fails
    result = scan_with(fake, market_limit=100)

    assert result.markets_scanned == 100
    assert result.diagnostics["clob_errors"] == 50  # the 50 markets in the failed chunk
    assert result.diagnostics["used_gamma_fallback"] == 50


class Clock:
    def __init__(self):
        self.now = 1_000.0

    def __call__(self):
        return self.now


class CountingScan:
    def __init__(self, delay: float = 0.0, fail_after: int = None):
        self.calls = 0
        self.delay = delay
        self.fail_after = fail_after

    async def __call__(self):
        self.calls += 1
        if self.delay:
            await asyncio.sleep(self.delay)
        if self.fail_after is not None and self.calls > self.fail_after:
            raise RuntimeError("Polymarket is down")
        return f"result {self.calls}"


def test_a_fresh_scan_is_reused_until_the_ttl_passes():
    clock, scan = Clock(), CountingScan()
    service = ScanService(cache=TTLCache(clock=clock), ttl=30, scan=scan)

    async def go():
        first = await service.latest()
        clock.now += 29
        second = await service.latest()
        clock.now += 2  # 31 s after the first scan
        third = await service.latest()
        return first, second, third

    assert asyncio.run(go()) == ("result 1", "result 1", "result 2")
    assert scan.calls == 2


def test_concurrent_requests_share_one_scan():
    scan = CountingScan(delay=0.05)
    service = ScanService(cache=TTLCache(), ttl=30, scan=scan)

    async def go():
        return await asyncio.gather(*(service.latest() for _ in range(10)))

    assert asyncio.run(go()) == ["result 1"] * 10
    assert scan.calls == 1


def test_a_failed_refresh_serves_the_previous_result():
    clock, scan = Clock(), CountingScan(fail_after=1)
    service = ScanService(cache=TTLCache(clock=clock), ttl=30, scan=scan)

    async def go():
        await service.latest()
        clock.now += 60
        return await service.latest()

    assert asyncio.run(go()) == "result 1"


def test_a_failure_with_nothing_cached_is_an_error():
    service = ScanService(cache=TTLCache(), ttl=30, scan=CountingScan(fail_after=0))
    with pytest.raises(RuntimeError):
        asyncio.run(service.latest())


def test_the_cache_works_across_event_loops():
    # A serverless runtime may run each request on a new event loop.
    clock, scan = Clock(), CountingScan()
    service = ScanService(cache=TTLCache(clock=clock), ttl=30, scan=scan)
    assert asyncio.run(service.latest()) == "result 1"
    assert asyncio.run(service.latest()) == "result 1"
    clock.now += 31
    assert asyncio.run(service.latest()) == "result 2"
