from __future__ import annotations
"""Arbitrage endpoints: the latest scan, its diagnostics, and a scan on demand."""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import get_settings
from app.core.scan import ScanResult, get_scan_service
from app.models.opportunity import Opportunity
from app.services.scanner import get_scanner

router = APIRouter(prefix="/arbitrage", tags=["arbitrage"])


class OpportunityResponse(BaseModel):
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
    yes_token_id: Optional[str] = None
    no_token_id: Optional[str] = None
    detected_at: datetime
    platform: str = "polymarket"


class ScanDiagnosticsResponse(BaseModel):
    """Why markets were set aside in the scan."""

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


class OpportunitiesResponse(BaseModel):
    opportunities: list[OpportunityResponse]
    count: int
    scan_time_ms: float
    scanned_at: datetime
    markets_scanned: int
    market_limit: int
    mode: str
    fee: float
    diagnostics: ScanDiagnosticsResponse


class ScannerStatsResponse(BaseModel):
    mode: str
    running: bool
    scan_count: int
    last_scan: Optional[str]
    active_opportunities: int
    total_seen: int


def _opportunity(o: Opportunity) -> OpportunityResponse:
    return OpportunityResponse(
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


def _diagnostics(result: ScanResult) -> ScanDiagnosticsResponse:
    return ScanDiagnosticsResponse(**result.diagnostics, threshold_percent=result.threshold * 100)


def _response(result: ScanResult) -> OpportunitiesResponse:
    return OpportunitiesResponse(
        opportunities=[_opportunity(o) for o in result.opportunities],
        count=len(result.opportunities),
        scan_time_ms=result.duration_ms,
        scanned_at=result.finished_at,
        markets_scanned=result.markets_scanned,
        market_limit=result.market_limit,
        mode=get_settings().resolved_mode,
        fee=result.fee,
        diagnostics=_diagnostics(result),
    )


async def _latest() -> ScanResult:
    """On request: the cached scan if fresh, else a new one.
    Continuous: whatever the loop produced last (waiting for its first scan)."""
    service = get_scan_service()
    if get_settings().resolved_mode == "continuous":
        return await service.latest(max_age=float("inf"))
    return await service.latest()


@router.get("/opportunities", response_model=OpportunitiesResponse)
async def get_opportunities():
    """Current opportunities among the most liquid two-outcome markets, with the scan's details."""
    return _response(await _latest())


@router.get("/opportunities/{opp_id}", response_model=OpportunityResponse)
async def get_opportunity(opp_id: str):
    opp = (await _latest()).get(opp_id)
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found in the latest scan")
    return _opportunity(opp)


@router.get("/diagnostics", response_model=ScanDiagnosticsResponse)
async def get_scan_diagnostics():
    """Why markets were set aside in the latest scan."""
    return _diagnostics(await _latest())


@router.get("/stats", response_model=ScannerStatsResponse)
async def get_scanner_stats():
    settings = get_settings()
    scanner = get_scanner()
    if scanner:
        return ScannerStatsResponse(mode=settings.resolved_mode, **scanner.stats)
    service = get_scan_service()
    last = service.peek()
    return ScannerStatsResponse(
        mode=settings.resolved_mode,
        running=False,
        scan_count=service.scan_count,
        last_scan=last.finished_at.isoformat() if last else None,
        active_opportunities=len(last.opportunities) if last else 0,
        total_seen=len(last.opportunities) if last else 0,
    )


@router.post("/scan", response_model=OpportunitiesResponse)
async def trigger_scan():
    """Continuous mode: scan now. On request: same as GET /opportunities, so a
    public deployment cannot be made to scan more than once per cache TTL."""
    if get_settings().resolved_mode == "continuous":
        scanner = get_scanner()
        if scanner:
            await scanner.scan_once()
            return _response(await _latest())
        return _response(await get_scan_service().fresh())
    return _response(await _latest())
