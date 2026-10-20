"""Application configuration."""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Literal, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

ScannerMode = Literal["auto", "continuous", "on_request"]


class Settings(BaseSettings):
    """Application settings loaded from environment variables (or a .env file)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # an old .env with keys that no longer exist still loads
    )

    app_name: str = "Prediction Market Arbitrage"

    # How scans run.
    # continuous: a background loop scans, keeps the latest result and alerts
    #             (for uvicorn on your own machine).
    # on_request: no loop; a request scans when the cached result is too old
    #             (for Vercel Functions, which hold no background work).
    # auto:       on_request on Vercel (the VERCEL variable is set), else continuous.
    scanner_mode: ScannerMode = "auto"

    # How many of the most liquid two-outcome markets one scan reads.
    # Unset: 200 on request, 1000 in the continuous loop.
    scan_market_limit: Optional[int] = None

    # How long a scan, a market list or a trade list is reused, in seconds.
    # On Vercel the same number is the CDN's s-maxage.
    cache_ttl_seconds: int = 30

    # Telegram alerts (both needed; without them alerts only print to the console).
    # Only the continuous loop sends alerts.
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None

    # Arbitrage detection
    min_profit_threshold: float = 0.01  # minimum net edge, as a fraction of cost (0.01 = 1%)
    scan_interval_seconds: int = 5  # continuous mode: pause between scans, not their length

    # Polymarket public APIs (read-only)
    gamma_api_url: str = "https://gamma-api.polymarket.com"
    clob_api_url: str = "https://clob.polymarket.com"

    @property
    def on_vercel(self) -> bool:
        return bool(os.environ.get("VERCEL"))

    @property
    def resolved_mode(self) -> Literal["continuous", "on_request"]:
        if self.scanner_mode == "auto":
            return "on_request" if self.on_vercel else "continuous"
        return self.scanner_mode

    @property
    def resolved_market_limit(self) -> int:
        if self.scan_market_limit:
            return max(1, self.scan_market_limit)
        return 200 if self.resolved_mode == "on_request" else 1000


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
