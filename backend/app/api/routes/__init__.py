"""API route modules."""
from .markets import router as markets_router
from .arbitrage import router as arbitrage_router
from .websocket import router as websocket_router
from .whales import router as whales_router
from .news import router as news_router

__all__ = [
    "markets_router",
    "arbitrage_router",
    "websocket_router",
    "whales_router",
    "news_router",
]
