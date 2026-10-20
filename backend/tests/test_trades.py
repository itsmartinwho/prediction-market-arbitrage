"""Tests for parsing Polymarket Data API trades. No network."""
from datetime import timezone

from app.clients.polymarket.data_client import DataClient

RAW = {
    "proxyWallet": "0x1234567890abcdef1234567890abcdef12345678",
    "side": "BUY",
    "conditionId": "0xabc",
    "size": 1000.0,
    "price": 0.5,
    "timestamp": 1792492991,  # the Data API sends unix seconds
    "title": "Will it rain tomorrow?",
    "slug": "rain-tomorrow",
    "eventSlug": "weather",
    "outcome": "Yes",
    "outcomeIndex": 0,
    "pseudonym": "Quiet-Heron",
}


def test_trade_keeps_its_own_time_not_now():
    trade = DataClient()._parse_trade(RAW)
    assert trade is not None
    assert trade.timestamp.tzinfo is timezone.utc
    assert int(trade.timestamp.timestamp()) == 1792492991


def test_trade_value_and_link():
    trade = DataClient()._parse_trade(RAW)
    assert trade.usd_value == 500.0
    assert trade.polymarket_url == "https://polymarket.com/event/weather"
    assert trade.trader_display_name == "Quiet-Heron"


def test_iso_timestamps_still_parse():
    trade = DataClient()._parse_trade({**RAW, "timestamp": "2026-10-20T10:00:00Z"})
    assert trade is not None
    assert trade.timestamp.hour == 10
