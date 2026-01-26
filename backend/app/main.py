"""FastAPI application entry point."""
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api.routes import markets_router, arbitrage_router, websocket_router, whales_router, news_router, market_activity_router
from app.api.routes.arbitrage import set_scanner
from app.services.scanner import OpportunityScanner
from app.services.notifications import TelegramNotifier, ConsoleNotifier, MultiNotifier

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global scanner task
_scanner_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global _scanner_task

    settings = get_settings()
    logger.info(f"Starting {settings.app_name}...")

    # Set up notifications
    notifier = MultiNotifier()
    notifier.add_notifier(ConsoleNotifier())

    if settings.telegram_bot_token and settings.telegram_chat_id:
        telegram = TelegramNotifier()
        notifier.add_notifier(telegram)
        logger.info("Telegram notifications enabled")

    # Create and start scanner
    scanner = OpportunityScanner(
        on_opportunity=notifier.send_opportunity_alert,
        scan_interval=settings.scan_interval_seconds,
    )
    set_scanner(scanner)

    # Start scanner in background
    _scanner_task = asyncio.create_task(scanner.start())
    logger.info("Background scanner started")

    yield

    # Shutdown
    logger.info("Shutting down...")
    await scanner.stop()
    if _scanner_task:
        _scanner_task.cancel()
        try:
            await _scanner_task
        except asyncio.CancelledError:
            pass


# Create FastAPI app
app = FastAPI(
    title="Prediction Market Arbitrage",
    description="Real-time arbitrage detection for Polymarket",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(markets_router, prefix="/api")
app.include_router(arbitrage_router, prefix="/api")
app.include_router(whales_router, prefix="/api")
app.include_router(news_router, prefix="/api")
app.include_router(market_activity_router, prefix="/api")
app.include_router(websocket_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Prediction Market Arbitrage",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    from app.api.routes.arbitrage import get_scanner

    scanner = get_scanner()
    return {
        "status": "healthy",
        "scanner_running": scanner.is_running if scanner else False,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
