"""Application configuration."""
from __future__ import annotations
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables (or a .env file)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # an old .env with keys that no longer exist still loads
    )

    app_name: str = "Prediction Market Arbitrage"

    # Telegram alerts (both needed; without them alerts only print to the console)
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None

    # Arbitrage detection
    min_profit_threshold: float = 0.01  # minimum net edge, as a fraction of cost (0.01 = 1%)
    scan_interval_seconds: int = 5  # pause between scans, not the length of a scan

    # Polymarket public APIs (read-only)
    gamma_api_url: str = "https://gamma-api.polymarket.com"
    clob_api_url: str = "https://clob.polymarket.com"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
