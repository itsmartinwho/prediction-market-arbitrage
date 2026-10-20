"""The endpoints as the dashboard and Vercel's CDN see them. Polymarket is faked."""
import httpx
import pytest
from fastapi.testclient import TestClient

from app.clients.polymarket import http as polymarket_http
from app.core.news_fetcher import NewsFetcher
from app.main import app
from tests.fake_polymarket import FakePolymarket


@pytest.fixture
def fake(monkeypatch):
    fake = FakePolymarket(n_markets=250)
    fake.events = [
        {"id": str(i), "title": f"Event {i}", "slug": f"event-{i}", "volume": 1000 - i, "volume24hr": 100 - i,
         "markets": [{"outcomePrices": '["0.%d", "0.%d"]' % (10 + i, 90 - i)}]}
        for i in range(30)
    ]
    monkeypatch.setattr(polymarket_http, "new_client", fake.client)

    async def no_headlines(self, titles, budget_seconds=4.0):
        return {}

    monkeypatch.setattr(NewsFetcher, "headlines_for", no_headlines)
    return fake


@pytest.fixture
def on_vercel(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")


def test_status_says_how_the_deployment_runs(fake, on_vercel):
    body = TestClient(app).get("/api/status").json()
    assert body["mode"] == "on_request"
    assert body["market_limit"] == 200
    assert body["alerts"] == "off"  # nothing alerts without the continuous loop


def test_status_off_vercel_is_the_continuous_loop(fake):
    body = TestClient(app).get("/api/status").json()
    assert body["mode"] == "continuous"
    assert body["market_limit"] == 1000
    assert body["alerts"] == "console"


def test_opportunities_are_scanned_once_and_cacheable_by_the_cdn(fake, on_vercel):
    client = TestClient(app)
    first = client.get("/api/arbitrage/opportunities")
    assert first.status_code == 200
    body = first.json()
    assert body["mode"] == "on_request"
    assert body["markets_scanned"] == 200 and body["market_limit"] == 200
    assert body["scanned_at"].endswith("Z") or "+00:00" in body["scanned_at"]
    assert body["diagnostics"]["total_markets"] == 200

    cache_control = first.headers["cache-control"]
    assert "s-maxage=30" in cache_control and "stale-while-revalidate=30" in cache_control
    assert "max-age=0" in cache_control  # browsers always ask again

    gamma_calls = len(fake.calls("/markets"))
    client.get("/api/arbitrage/opportunities")
    client.get("/api/arbitrage/diagnostics")
    client.post("/api/arbitrage/scan")  # on request, a POST does not force a scan
    assert len(fake.calls("/markets")) == gamma_calls


def test_hot_and_movers_share_one_gamma_request(fake, on_vercel):
    client = TestClient(app)
    hot = client.get("/api/market-activity/hot?limit=5").json()
    movers = client.get("/api/market-activity/movers?limit=5").json()
    assert [m["title"] for m in hot["markets"]] == ["Event 0", "Event 1", "Event 2", "Event 3", "Event 4"]
    assert movers["count"] == 5 and hot["fetched_at"] == movers["fetched_at"]
    assert len(fake.calls("/events")) == 1


def test_an_upstream_failure_is_an_error_not_an_empty_list(fake, on_vercel, monkeypatch):
    def broken(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"error": "down"})

    monkeypatch.setattr(polymarket_http, "new_client", lambda: httpx.AsyncClient(transport=httpx.MockTransport(broken)))
    response = TestClient(app).get("/api/whales/activity")
    assert response.status_code == 502
    assert "data-api.polymarket.com/trades" in response.json()["detail"]
    assert response.headers["cache-control"] == "no-store"  # the CDN must not keep an error


def test_the_websocket_endpoints_are_gone(fake):
    assert TestClient(app).get("/ws/opportunities").status_code == 404
