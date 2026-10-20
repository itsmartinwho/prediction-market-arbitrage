"""Tests for the YES + NO detector. No network: the price sources are stubs."""
import asyncio
import pathlib
import re

from app.core.arbitrage import YesNoArbitrageDetector
from app.models.market import Market, Token
from app.models.opportunity import OpportunityType


class StubGamma:
    async def close(self):
        pass


class StubCLOB:
    """Returns fixed best asks per token id; a missing id means an empty book."""

    def __init__(self, asks):
        self.asks = asks

    async def get_best_ask(self, token_id):
        return self.asks.get(token_id)

    async def close(self):
        pass


def market(yes_price=None, no_price=None, binary=True):
    return Market(
        id="m1",
        question="Will it rain tomorrow?",
        yes_token=Token(token_id="yes", outcome="Yes") if binary else None,
        no_token=Token(token_id="no", outcome="No") if binary else None,
        yes_price=yes_price,
        no_price=no_price,
    )


def scan(m, asks, threshold=0.01, gamma_fallback=True):
    detector = YesNoArbitrageDetector(
        gamma_client=StubGamma(),
        clob_client=StubCLOB(asks),
        min_profit_threshold=threshold,
        use_gamma_fallback=gamma_fallback,
    )
    return asyncio.run(detector.scan_market(m)), detector


def test_finds_an_edge_after_the_fee():
    # 0.48 + 0.49 = 0.97 -> 0.03 gross, minus the assumed 0.02 fee = 0.01 net
    opp, _ = scan(market(), {"yes": 0.48, "no": 0.49})
    assert opp is not None
    assert opp.type == OpportunityType.YES_NO
    assert round(opp.combined_cost, 4) == 0.97
    assert round(opp.gross_profit, 4) == 0.03
    assert round(opp.net_profit, 4) == 0.01
    assert round(opp.edge_percent, 2) == 1.03


def test_no_edge_when_the_fee_eats_the_spread():
    # 0.99 total is under $1 but the 0.02 fee makes it a loss
    opp, detector = scan(market(), {"yes": 0.50, "no": 0.49})
    assert opp is None
    assert detector.diagnostics.not_profitable == 1


def test_edge_below_the_threshold_is_skipped():
    # 0.975 total -> 0.005 net, 0.51% of cost, under the 1% threshold
    opp, detector = scan(market(), {"yes": 0.485, "no": 0.49})
    assert opp is None
    assert detector.diagnostics.below_threshold == 1


def test_non_binary_market_is_skipped():
    opp, detector = scan(market(binary=False), {})
    assert opp is None
    assert detector.diagnostics.not_binary == 1


def test_falls_back_to_gamma_prices_when_the_book_is_empty():
    m = market(yes_price=0.40, no_price=0.50)
    opp, detector = scan(m, {})
    assert opp is not None
    assert round(opp.combined_cost, 2) == 0.90
    assert detector.diagnostics.used_gamma_fallback == 1


def test_no_fallback_means_no_opportunity():
    m = market(yes_price=0.40, no_price=0.50)
    opp, _ = scan(m, {}, gamma_fallback=False)
    assert opp is None


def test_alert_message_has_the_prices():
    opp, _ = scan(market(), {"yes": 0.48, "no": 0.49})
    text = opp.to_alert_message()
    assert "Will it rain tomorrow?" in text
    assert "$0.4800" in text and "$0.4900" in text and "$0.9700" in text


def test_the_app_has_no_trading_or_signing_code():
    """The app only reads public data. Fail if anything that could sign or
    place an order, or read a wallet key, gets added."""
    banned = re.compile(
        r"py_clob_client|eth_account|web3|private_key|create_order|post_order",
        re.IGNORECASE,
    )
    app_dir = pathlib.Path(__file__).resolve().parent.parent / "app"
    hits = [
        str(p.relative_to(app_dir))
        for p in app_dir.rglob("*.py")
        if banned.search(p.read_text())
    ]
    assert hits == []
