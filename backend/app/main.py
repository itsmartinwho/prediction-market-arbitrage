"""FastAPI application entry point.

Two ways to run it, one code path for the scan (app/core/scan.py):

- on_request (on Vercel): no background work. An endpoint scans or fetches
  when its cached result is older than CACHE_TTL_SECONDS, and responses carry
  Cache-Control so Vercel's CDN answers most requests without the function.
- continuous (uvicorn on your machine): a loop scans every few seconds and
  sends alerts to the console, and to Telegram when it is configured.
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from urllib.parse import urlsplit

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import (
    arbitrage_router,
    market_activity_router,
    markets_router,
    news_router,
    whales_router,
)
from app.config import get_settings
from app.core.arbitrage import YesNoArbitrageDetector
from app.services.notifications import ConsoleNotifier, MultiNotifier, TelegramNotifier
from app.services.scanner import OpportunityScanner, get_scanner, set_scanner

VERSION = "0.3.0"
REQUEST_TIMEOUT_SECONDS = 25  # well inside the function's maxDuration (vercel.json)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def _alerts(settings) -> str:
    if settings.resolved_mode != "continuous":
        return "off"
    if settings.telegram_bot_token and settings.telegram_chat_id:
        return "telegram"
    return "console"


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    mode = settings.resolved_mode
    logger.info(f"Starting {settings.app_name} in {mode} mode ({settings.resolved_market_limit} markets per scan)")

    task = None
    if mode == "continuous":
        notifier = MultiNotifier()
        notifier.add_notifier(ConsoleNotifier())
        if _alerts(settings) == "telegram":
            notifier.add_notifier(TelegramNotifier())
            logger.info("Telegram alerts on")
        scanner = OpportunityScanner(on_opportunity=notifier.send_opportunity_alert)
        set_scanner(scanner)
        task = asyncio.create_task(scanner.start())

    yield

    scanner = get_scanner()
    if scanner:
        await scanner.stop()
        set_scanner(None)
    if task:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="Prediction Market Arbitrage",
    description="YES + NO arbitrage detection, whale trades and signals for Polymarket. Read-only.",
    version=VERSION,
    lifespan=lifespan,
    # Under /api so they are reachable on Vercel too, where only /api/* reaches Python
    docs_url="/api/docs",
    redoc_url=None,
    openapi_url="/api/openapi.json",
)

# The dashboard calls the API on its own origin. This only matters for a
# frontend served from somewhere else; nothing here uses cookies.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.middleware("http")
async def time_limit_and_cache(request: Request, call_next):
    """Give up cleanly after REQUEST_TIMEOUT_SECONDS, and let the CDN cache
    successful GETs for the same TTL the in-memory cache uses."""
    try:
        response = await asyncio.wait_for(call_next(request), timeout=REQUEST_TIMEOUT_SECONDS)
    except asyncio.TimeoutError:
        return JSONResponse(
            status_code=504,
            content={"detail": f"Polymarket did not answer within {REQUEST_TIMEOUT_SECONDS} seconds"},
            headers={"Cache-Control": "no-store"},
        )
    if (
        request.method == "GET"
        and request.url.path.startswith("/api/")
        and response.status_code == 200
        and "cache-control" not in response.headers
    ):
        ttl = get_settings().cache_ttl_seconds
        # Browsers revalidate every time (max-age=0); Vercel's CDN keeps the
        # response for ttl seconds and serves it stale for ttl more while it
        # fetches a new one in the background.
        response.headers["Cache-Control"] = f"public, max-age=0, s-maxage={ttl}, stale-while-revalidate={ttl}"
    elif "cache-control" not in response.headers:
        response.headers["Cache-Control"] = "no-store"
    return response


def _where(exc: httpx.RequestError) -> str:
    """host/path of the upstream request that failed (no query string)."""
    try:
        parts = urlsplit(str(exc.request.url))
    except RuntimeError:  # an error raised before a request existed
        return "Polymarket"
    return f"{parts.netloc}{parts.path}"


@app.exception_handler(httpx.HTTPStatusError)
async def upstream_status(request: Request, exc: httpx.HTTPStatusError):
    return JSONResponse(
        status_code=502,
        content={"detail": f"{_where(exc)} answered {exc.response.status_code}"},
    )


@app.exception_handler(httpx.TransportError)
async def upstream_unreachable(request: Request, exc: httpx.TransportError):
    timeout = isinstance(exc, httpx.TimeoutException)
    return JSONResponse(
        status_code=504 if timeout else 502,
        content={"detail": f"{_where(exc)} {'timed out' if timeout else 'could not be reached'}"},
    )


app.include_router(markets_router, prefix="/api")
app.include_router(arbitrage_router, prefix="/api")
app.include_router(whales_router, prefix="/api")
app.include_router(news_router, prefix="/api")
app.include_router(market_activity_router, prefix="/api")


@app.get("/api/status")
async def status():
    """How this deployment runs. Reads nothing from Polymarket."""
    settings = get_settings()
    return {
        "status": "ok",
        "version": VERSION,
        "mode": settings.resolved_mode,
        "on_vercel": settings.on_vercel,
        "market_limit": settings.resolved_market_limit,
        "cache_ttl_seconds": settings.cache_ttl_seconds,
        "scan_interval_seconds": settings.scan_interval_seconds if settings.resolved_mode == "continuous" else None,
        "min_profit_threshold": settings.min_profit_threshold,
        "fee": YesNoArbitrageDetector.POLYMARKET_FEE,
        "alerts": _alerts(settings),
    }


@app.get("/api/health")
@app.get("/health")
async def health():
    scanner = get_scanner()
    return {
        "status": "healthy",
        "mode": get_settings().resolved_mode,
        "scanner_running": scanner.is_running if scanner else False,
    }


@app.get("/")
async def root():
    return {"name": "Prediction Market Arbitrage", "version": VERSION, "docs": "/api/docs"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
