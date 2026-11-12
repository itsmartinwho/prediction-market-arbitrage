"""Tests for the YES + NO detector. No network: the price sources are stubs."""
import asyncio
import pathlib
import re

from app.core.arbitrage import YesNoArbitrageDetector
from app.core.arbitrage.yes_no_arb import compute_book_depth
from app.models.market import Market, OrderBook, OrderBookLevel, Token
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


def test_order_book_depth_and_closest_markets():
    yes_book = OrderBook(
        token_id="yes",
        asks=[
            OrderBookLevel(price=0.47, size=120.0),
            OrderBookLevel(price=0.48, size=80.0),
            OrderBookLevel(price=0.52, size=500.0),
        ],
    )
    no_book = OrderBook(
        token_id="no",
        asks=[
            OrderBookLevel(price=0.49, size=100.0),
            OrderBookLevel(price=0.49, size=60.0),
            OrderBookLevel(price=0.51, size=500.0),
        ],
    )
    best_size, max_size, max_profit, vwap_cost = compute_book_depth(yes_book, no_book, fee=0.02)
    assert best_size == 100.0
    # 100 shares @ (0.47+0.49=0.96, net 0.02) -> $2.00
    # 20 shares @ (0.47+0.49=0.96, net 0.02) -> $0.40
    # 40 shares @ (0.48+0.49=0.97, net 0.01) -> $0.40
    # Next level is 0.48+0.51=0.99 (net -0.01), stops.
    assert max_size == 160.0
    assert max_profit == 2.8
    assert round(vwap_cost, 4) == 0.9625

    detector = YesNoArbitrageDetector(min_profit_threshold=0.01)
    opp = detector.evaluate(market(), 0.47, 0.49, yes_book=yes_book, no_book=no_book)
    assert opp is not None
    assert opp.best_ask_size == 100.0
    assert opp.max_executable_size == 160.0
    assert opp.max_executable_profit == 2.8
    diag = detector.get_diagnostics()
    assert len(diag["closest_markets"]) == 1
    assert diag["closest_markets"][0]["combined_cost"] == 0.96


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


def test_the_only_post_is_the_order_book_read():
    """Every request is a GET except CLOB's /books, which posts a list of token
    ids to read their order books. Fail if any other POST appears."""
    app_dir = pathlib.Path(__file__).resolve().parent.parent / "app"
    posts = []
    for p in app_dir.rglob("*.py"):
        for line in p.read_text().splitlines():
            code = line.split("#", 1)[0].strip()
            if code.startswith("@"):  # this API's own POST routes, not outgoing requests
                continue
            if re.search(r"\.post\(|post_json\(", code) and "def post_json" not in code:
                posts.append((p.name, code))
    # http.py's helper itself, and the one call that uses it
    assert all(name == "http.py" or "/books" in code for name, code in posts), posts
    callers = [code for name, code in posts if name != "http.py"]
    assert len(callers) == 1 and "/books" in callers[0], callers
