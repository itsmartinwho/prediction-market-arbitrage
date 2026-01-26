"""Application configuration."""
from __future__ import annotations
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App
    app_name: str = "Prediction Market Arbitrage"
    debug: bool = False

    # Database
    database_url: str = "sqlite+aiosqlite:///./arb.db"

    # Polymarket
    polymarket_private_key: Optional[str] = None

    # Telegram
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None

    # Arbitrage Detection
    min_profit_threshold: float = 0.01  # 1% minimum edge (lowered to surface more opportunities)
    scan_interval_seconds: int = 5

    # Risk Management (conservative for paper trading)
    max_position_per_market: float = 50.0
    max_global_exposure: float = 500.0
    max_daily_loss: float = 50.0
    enable_auto_execute: bool = False

    # API URLs
    gamma_api_url: str = "https://gamma-api.polymarket.com"
    clob_api_url: str = "https://clob.polymarket.com"
    clob_ws_url: str = "wss://ws-subscriptions-clob.polymarket.com/ws/market"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
