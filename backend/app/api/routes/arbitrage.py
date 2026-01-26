from __future__ import annotations
"""Arbitrage endpoints."""
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.arbitrage import YesNoArbitrageDetector
from app.services.scanner import FastScanner

router = APIRouter(prefix="/arbitrage", tags=["arbitrage"])


class OpportunityResponse(BaseModel):
    """Arbitrage opportunity response."""

    id: str
    type: str
    market_id: str
    market_question: str
    yes_price: float
    no_price: float
    combined_cost: float
    gross_profit: float
    net_profit: float
    edge_percent: float
    yes_token_id: str | None = None
    no_token_id: str | None = None
    detected_at: datetime
    platform: str = "polymarket"


class OpportunitiesResponse(BaseModel):
    """List of opportunities response."""

    opportunities: list[OpportunityResponse]
    count: int
    scan_time_ms: float


class ScannerStatsResponse(BaseModel):
    """Scanner statistics response."""

    running: bool
    scan_count: int
    last_scan: str | None
    active_opportunities: int
    total_seen: int


class ScanDiagnosticsResponse(BaseModel):
    """Scan diagnostics response - shows why markets are filtered."""

    total_markets: int
    filtered_not_binary: int
    filtered_no_tokens: int
    filtered_no_clob_liquidity: int
    clob_errors: int
    used_gamma_fallback: int
    filtered_not_profitable: int
    filtered_below_threshold: int
    opportunities_found: int
    threshold_percent: float


# Global scanner instance (will be initialized in main.py)
_scanner = None


def get_scanner():
    """Get the global scanner instance."""
    global _scanner
    return _scanner


def set_scanner(scanner):
    """Set the global scanner instance."""
    global _scanner
    _scanner = scanner


@router.get("/opportunities", response_model=OpportunitiesResponse)
async def get_opportunities():
    """
    Get current arbitrage opportunities.

    If the background scanner is running, returns cached opportunities.
    Otherwise, runs a quick scan using Gamma API prices.
    """
    scanner = get_scanner()

    if scanner and scanner.is_running:
        # Return cached opportunities from background scanner
        opps = scanner.get_opportunities()
        return OpportunitiesResponse(
            opportunities=[
                OpportunityResponse(
                    id=o.id,
                    type=o.type.value,
                    market_id=o.market_id,
                    market_question=o.market_question,
                    yes_price=o.yes_price,
                    no_price=o.no_price,
                    combined_cost=o.combined_cost,
                    gross_profit=o.gross_profit,
                    net_profit=o.net_profit,
                    edge_percent=o.edge_percent,
                    yes_token_id=o.yes_token_id,
                    no_token_id=o.no_token_id,
                    detected_at=o.detected_at,
                    platform=o.platform,
                )
                for o in opps
            ],
            count=len(opps),
            scan_time_ms=0,  # Cached, no scan time
        )

    # Run a quick scan
    start = datetime.utcnow()
    fast_scanner = FastScanner()

    try:
        opps = await fast_scanner.scan()
        scan_time = (datetime.utcnow() - start).total_seconds() * 1000

        return OpportunitiesResponse(
            opportunities=[
                OpportunityResponse(
                    id=o.id,
                    type=o.type.value,
                    market_id=o.market_id,
                    market_question=o.market_question,
                    yes_price=o.yes_price,
                    no_price=o.no_price,
                    combined_cost=o.combined_cost,
                    gross_profit=o.gross_profit,
                    net_profit=o.net_profit,
                    edge_percent=o.edge_percent,
                    yes_token_id=o.yes_token_id,
                    no_token_id=o.no_token_id,
                    detected_at=o.detected_at,
                    platform=o.platform,
                )
                for o in opps
            ],
            count=len(opps),
            scan_time_ms=scan_time,
        )
    finally:
        await fast_scanner.close()


@router.get("/opportunities/{opp_id}", response_model=OpportunityResponse)
async def get_opportunity(opp_id: str):
    """Get a specific opportunity by ID."""
    scanner = get_scanner()

    if not scanner:
        raise HTTPException(status_code=503, detail="Scanner not running")

    opp = scanner.get_opportunity(opp_id)
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    return OpportunityResponse(
        id=opp.id,
        type=opp.type.value,
        market_id=opp.market_id,
        market_question=opp.market_question,
        yes_price=opp.yes_price,
        no_price=opp.no_price,
        combined_cost=opp.combined_cost,
        gross_profit=opp.gross_profit,
        net_profit=opp.net_profit,
        edge_percent=opp.edge_percent,
        yes_token_id=opp.yes_token_id,
        no_token_id=opp.no_token_id,
        detected_at=opp.detected_at,
        platform=opp.platform,
    )


@router.get("/stats", response_model=ScannerStatsResponse)
async def get_scanner_stats():
    """Get scanner statistics."""
    scanner = get_scanner()

    if not scanner:
        return ScannerStatsResponse(
            running=False,
            scan_count=0,
            last_scan=None,
            active_opportunities=0,
            total_seen=0,
        )

    stats = scanner.stats
    return ScannerStatsResponse(**stats)


@router.post("/scan")
async def trigger_scan():
    """
    Trigger an immediate scan.

    Returns the opportunities found.
    """
    scanner = get_scanner()

    if scanner:
        opps = await scanner.scan_once()
    else:
        fast_scanner = FastScanner()
        try:
            opps = await fast_scanner.scan()
        finally:
            await fast_scanner.close()

    return {
        "message": "Scan complete",
        "opportunities_found": len(opps),
        "opportunities": [
            {
                "id": o.id,
                "market": o.market_question[:50],
                "edge": f"{o.edge_percent:.2f}%",
            }
            for o in opps[:10]  # Top 10
        ],
    }


@router.get("/diagnostics", response_model=ScanDiagnosticsResponse)
async def get_scan_diagnostics():
    """
    Get diagnostics from the last scan.

    Shows why markets were filtered (no liquidity, not profitable, etc.)
    Useful for understanding why there are no opportunities.
    """
    from app.config import get_settings

    scanner = get_scanner()
    settings = get_settings()

    if not scanner:
        return ScanDiagnosticsResponse(
            total_markets=0,
            filtered_not_binary=0,
            filtered_no_tokens=0,
            filtered_no_clob_liquidity=0,
            clob_errors=0,
            used_gamma_fallback=0,
            filtered_not_profitable=0,
            filtered_below_threshold=0,
            opportunities_found=0,
            threshold_percent=settings.min_profit_threshold * 100,
        )

    diag = scanner.detector.get_diagnostics()
    return ScanDiagnosticsResponse(
        total_markets=diag.get("total_markets", 0),
        filtered_not_binary=diag.get("filtered_not_binary", 0),
        filtered_no_tokens=diag.get("filtered_no_tokens", 0),
        filtered_no_clob_liquidity=diag.get("filtered_no_clob_liquidity", 0),
        clob_errors=diag.get("clob_errors", 0),
        used_gamma_fallback=diag.get("used_gamma_fallback", 0),
        filtered_not_profitable=diag.get("filtered_not_profitable", 0),
        filtered_below_threshold=diag.get("filtered_below_threshold", 0),
        opportunities_found=diag.get("opportunities_found", 0),
        threshold_percent=settings.min_profit_threshold * 100,
    )
