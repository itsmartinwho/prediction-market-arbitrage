import pathlib

import pytest

from app import config
from app.core import cache, scan


@pytest.fixture(autouse=True)
def clean_state(monkeypatch):
    """Every test starts with default settings, an empty cache and no scan service,
    whatever the environment says."""
    for name in ("SCANNER_MODE", "SCAN_MARKET_LIMIT", "CACHE_TTL_SECONDS", "MIN_PROFIT_THRESHOLD",
                 "VERCEL", "GAMMA_API_URL", "CLOB_API_URL", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.chdir(pathlib.Path(__file__).parent)  # so no stray .env is read
    config.get_settings.cache_clear()
    cache.shared_cache().clear()
    scan._service = None
    yield
    config.get_settings.cache_clear()
    cache.shared_cache().clear()
    scan._service = None
