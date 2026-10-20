from __future__ import annotations
"""YES + NO arbitrage detection.

In a two-outcome market exactly one side pays $1.00. If the best ask for YES
plus the best ask for NO is under $1.00 by more than the fee, buying both
locks in the difference:

    cost  = yes_ask + no_ask
    gross = 1.00 - cost
    net   = gross - fee        (an assumed flat $0.02 per $1 of payout)
    edge  = net / cost

Example: YES 0.48 + NO 0.49 = 0.97, so 0.03 gross, 0.01 net, a 1.03% edge.
"""
import logging
from datetime import datetime, timezone
from typing import List, Optional

from app.config import get_settings
from app.models.market import Market
from app.models.opportunity import Opportunity, OpportunityType

logger = logging.getLogger(__name__)


class ScanDiagnostics:
    """Counts why markets were set aside during a scan."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.total_markets = 0
        self.not_binary = 0
        self.no_tokens = 0
        self.no_clob_liquidity = 0
        self.clob_errors = 0
        self.used_gamma_fallback = 0
        self.not_profitable = 0
        self.below_threshold = 0
        self.opportunities_found = 0

    def to_dict(self) -> dict:
        return {
            "total_markets": self.total_markets,
            "filtered_not_binary": self.not_binary,
            "filtered_no_tokens": self.no_tokens,
            "filtered_no_clob_liquidity": self.no_clob_liquidity,
            "clob_errors": self.clob_errors,
            "used_gamma_fallback": self.used_gamma_fallback,
            "filtered_not_profitable": self.not_profitable,
            "filtered_below_threshold": self.below_threshold,
            "opportunities_found": self.opportunities_found,
        }


class YesNoArbitrageDetector:
    """
    Finds YES + NO < $1 after the fee in two-outcome Polymarket markets.

    Prices are the best asks from the CLOB order books. When a book is empty
    or its request fails, the detector can fall back to the prices Gamma lists
    (last or mid prices, which you cannot necessarily buy at); diagnostics
    count every fallback. It only reads prices: there is nothing here that
    trades.
    """

    # Assumed fee: a flat $0.02 per $1.00 of payout. Not read from Polymarket.
    POLYMARKET_FEE = 0.02

    def __init__(
        self,
        gamma_client=None,
        clob_client=None,
        min_profit_threshold: Optional[float] = None,
        use_gamma_fallback: bool = True,
    ):
        self.gamma = gamma_client
        self.clob = clob_client
        self.use_gamma_fallback = use_gamma_fallback
        self.min_profit_threshold = (
            min_profit_threshold if min_profit_threshold is not None
            else get_settings().min_profit_threshold
        )
        self.diagnostics = ScanDiagnostics()

    async def close(self):
        for client in (self.gamma, self.clob):
            if client is not None:
                await client.close()

    def evaluate(
        self,
        market: Market,
        yes_ask: Optional[float],
        no_ask: Optional[float],
        clob_failed: bool = False,
    ) -> Optional[Opportunity]:
        """Apply the YES + NO test to one market's asks. Counts into diagnostics."""
        if clob_failed:
            self.diagnostics.clob_errors += 1

        used_fallback = False
        if (yes_ask is None or no_ask is None) and self.use_gamma_fallback:
            if market.yes_price is not None and market.no_price is not None:
                yes_ask, no_ask = market.yes_price, market.no_price
                used_fallback = True
                self.diagnostics.used_gamma_fallback += 1

        if yes_ask is None or no_ask is None:
            self.diagnostics.no_clob_liquidity += 1
            return None

        combined_cost = yes_ask + no_ask
        gross_profit = 1.0 - combined_cost
        net_profit = gross_profit - self.POLYMARKET_FEE
        edge_percent = (net_profit / combined_cost * 100) if combined_cost > 0 else 0

        if net_profit <= 0:
            self.diagnostics.not_profitable += 1
            return None

        if edge_percent < self.min_profit_threshold * 100:
            self.diagnostics.below_threshold += 1
            return None

        self.diagnostics.opportunities_found += 1
        logger.info(
            f"Opportunity in {market.question[:50]}: cost ${combined_cost:.4f}, "
            f"net ${net_profit:.4f} ({edge_percent:.2f}%)"
            f"{' [Gamma prices]' if used_fallback else ''}"
        )
        return Opportunity(
            type=OpportunityType.YES_NO,
            market_id=market.id,
            market_question=market.question,
            yes_price=yes_ask,
            no_price=no_ask,
            combined_cost=combined_cost,
            gross_profit=gross_profit,
            net_profit=net_profit,
            edge_percent=edge_percent,
            yes_token_id=market.yes_token.token_id if market.yes_token else None,
            no_token_id=market.no_token.token_id if market.no_token else None,
            detected_at=datetime.now(timezone.utc),
            platform="polymarket",
        )

    def _usable(self, market: Market) -> bool:
        if not market.is_binary:
            self.diagnostics.not_binary += 1
            return False
        if not market.yes_token or not market.no_token:
            self.diagnostics.no_tokens += 1
            return False
        return True

    async def scan_market(self, market: Market) -> Optional[Opportunity]:
        """Check one market, reading its two order books one by one."""
        if not self._usable(market):
            return None
        yes_ask = no_ask = None
        failed = False
        try:
            yes_ask = await self.clob.get_best_ask(market.yes_token.token_id)
            no_ask = await self.clob.get_best_ask(market.no_token.token_id)
        except Exception as e:
            logger.warning(f"CLOB error for market {market.id}: {e}")
            failed = True
        return self.evaluate(market, yes_ask, no_ask, clob_failed=failed)

    async def scan_markets(self, markets: List[Market]) -> List[Opportunity]:
        """Check many markets, reading all their order books in batches.

        Resets the diagnostics, so they describe this call alone.
        """
        self.diagnostics.reset()
        self.diagnostics.total_markets = len(markets)

        usable = [m for m in markets if self._usable(m)]
        token_ids = [t for m in usable for t in (m.yes_token.token_id, m.no_token.token_id)]
        batch = await self.clob.get_order_books(token_ids)

        opportunities = []
        for market in usable:
            yes_id, no_id = market.yes_token.token_id, market.no_token.token_id
            yes_book, no_book = batch.books.get(yes_id), batch.books.get(no_id)
            opp = self.evaluate(
                market,
                yes_book.best_ask if yes_book else None,
                no_book.best_ask if no_book else None,
                clob_failed=yes_id in batch.failed or no_id in batch.failed,
            )
            if opp:
                opportunities.append(opp)

        opportunities.sort(key=lambda x: x.edge_percent, reverse=True)
        return opportunities

    def get_diagnostics(self) -> dict:
        """The diagnostics of the last scan."""
        return self.diagnostics.to_dict()
