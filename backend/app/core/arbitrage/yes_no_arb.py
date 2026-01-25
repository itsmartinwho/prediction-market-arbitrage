from __future__ import annotations
"""YES + NO arbitrage detection.

This is the core arbitrage strategy:
- In a binary market, YES + NO should sum to ~$1.00
- If YES ask + NO ask < $1.00, buy both for guaranteed profit
- Example: YES @ $0.48 + NO @ $0.49 = $0.97 total
- Payout is $1.00, so gross profit = $0.03 (3.09%)
- After Polymarket's 2% fee on winning side: ~1% net profit

Key insight: One side ALWAYS wins, so you're guaranteed the $1 payout.
"""
import logging
from datetime import datetime

from app.config import get_settings
from app.models.market import Market
from app.models.opportunity import Opportunity, OpportunityType
from app.clients.polymarket import GammaClient, CLOBClient

logger = logging.getLogger(__name__)


class YesNoArbitrageDetector:
    """
    Detects YES+NO arbitrage opportunities on Polymarket.

    Strategy:
    1. Fetch active binary markets
    2. For each market, get YES and NO ask prices
    3. If combined cost < $1.00 - fees, it's an opportunity
    4. Alert the user for manual execution

    Fee structure:
    - Polymarket charges 2% on profitable outcomes
    - Since one side always wins, we pay one 2% fee
    - Need edge > 2.5% to be profitable after fees
    """

    # Polymarket fee on winning trades
    POLYMARKET_FEE = 0.02

    def __init__(
        self,
        gamma_client: GammaClient | None = None,
        clob_client: CLOBClient | None = None,
        min_profit_threshold: float | None = None,
    ):
        self.gamma = gamma_client or GammaClient()
        self.clob = clob_client or CLOBClient()

        settings = get_settings()
        self.min_profit_threshold = (
            min_profit_threshold or settings.min_profit_threshold
        )

    async def close(self):
        """Clean up clients."""
        await self.gamma.close()
        await self.clob.close()

    async def scan_market(self, market: Market) -> Opportunity | None:
        """
        Scan a single market for YES+NO arbitrage.

        Args:
            market: Market to scan

        Returns:
            Opportunity if profitable, None otherwise
        """
        if not market.is_binary:
            return None

        if not market.yes_token or not market.no_token:
            return None

        try:
            # Get best ask prices (what we'd pay to buy)
            yes_ask = await self.clob.get_best_ask(market.yes_token.token_id)
            no_ask = await self.clob.get_best_ask(market.no_token.token_id)

            if yes_ask is None or no_ask is None:
                logger.debug(f"No liquidity for market {market.id}")
                return None

            # Calculate profitability
            combined_cost = yes_ask + no_ask
            gross_profit = 1.0 - combined_cost

            # After fee (2% on the winning side = $1.00 * 0.02 = $0.02)
            net_profit = gross_profit - self.POLYMARKET_FEE

            # Edge as percentage of cost
            edge_percent = (net_profit / combined_cost * 100) if combined_cost > 0 else 0

            # Check if profitable
            if net_profit <= 0:
                return None

            if edge_percent < self.min_profit_threshold * 100:
                logger.debug(
                    f"Market {market.id}: edge {edge_percent:.2f}% below threshold"
                )
                return None

            logger.info(
                f"🎯 Found opportunity in {market.question[:50]}... "
                f"Cost: ${combined_cost:.4f}, Net profit: ${net_profit:.4f} ({edge_percent:.2f}%)"
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
                yes_token_id=market.yes_token.token_id,
                no_token_id=market.no_token.token_id,
                detected_at=datetime.utcnow(),
                platform="polymarket",
            )

        except Exception as e:
            logger.warning(f"Error scanning market {market.id}: {e}")
            return None

    async def scan_all_markets(self) -> list[Opportunity]:
        """
        Scan all active markets for arbitrage opportunities.

        Returns:
            List of opportunities sorted by edge (highest first)
        """
        logger.info("Starting full market scan...")

        # Fetch all active binary markets
        markets = await self.gamma.get_all_active_markets()
        logger.info(f"Fetched {len(markets)} active binary markets")

        opportunities = []
        for market in markets:
            opp = await self.scan_market(market)
            if opp:
                opportunities.append(opp)

        # Sort by edge (best opportunities first)
        opportunities.sort(key=lambda x: x.edge_percent, reverse=True)

        logger.info(f"Found {len(opportunities)} arbitrage opportunities")
        return opportunities

    async def scan_markets_fast(self, markets: list[Market]) -> list[Opportunity]:
        """
        Quick scan using Gamma API prices (less accurate but faster).

        Uses the prices already in the Market objects from Gamma API,
        rather than fetching fresh order book data from CLOB.
        Good for initial filtering before detailed scanning.
        """
        opportunities = []

        for market in markets:
            if not market.is_binary:
                continue

            yes_price = market.yes_price
            no_price = market.no_price

            if yes_price is None or no_price is None:
                continue

            combined_cost = yes_price + no_price
            gross_profit = 1.0 - combined_cost
            net_profit = gross_profit - self.POLYMARKET_FEE
            edge_percent = (net_profit / combined_cost * 100) if combined_cost > 0 else 0

            if net_profit > 0 and edge_percent >= self.min_profit_threshold * 100:
                opportunities.append(
                    Opportunity(
                        type=OpportunityType.YES_NO,
                        market_id=market.id,
                        market_question=market.question,
                        yes_price=yes_price,
                        no_price=no_price,
                        combined_cost=combined_cost,
                        gross_profit=gross_profit,
                        net_profit=net_profit,
                        edge_percent=edge_percent,
                        yes_token_id=market.yes_token.token_id if market.yes_token else None,
                        no_token_id=market.no_token.token_id if market.no_token else None,
                        detected_at=datetime.utcnow(),
                        platform="polymarket",
                    )
                )

        opportunities.sort(key=lambda x: x.edge_percent, reverse=True)
        return opportunities
