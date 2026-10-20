"""One HTTP setup for every call to Polymarket's public APIs.

Timeouts are short and there is one quick retry, so a request on Vercel either
answers within seconds or fails with a clear error rather than hanging.

Every call reads. All of them are GETs except CLOB's /books, which takes its
list of token ids in a POST body and returns their order books; nothing here
signs anything or places an order.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Optional

import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_fixed

TIMEOUT = httpx.Timeout(10.0, connect=5.0)
RETRY_STATUSES = {429, 500, 502, 503, 504}


def new_client() -> httpx.AsyncClient:
    """A client for one unit of work (a scan, a list refresh).

    Clients are made per unit of work rather than kept globally, so nothing is
    tied to an event loop that a serverless runtime may have replaced.
    """
    return httpx.AsyncClient(
        timeout=TIMEOUT,
        headers={"Accept": "application/json"},
        follow_redirects=True,
        limits=httpx.Limits(max_connections=20, max_keepalive_connections=20),
    )


@asynccontextmanager
async def session(http: Optional[httpx.AsyncClient] = None) -> AsyncIterator[httpx.AsyncClient]:
    """Use the client passed in, or make one for the duration of the block."""
    if http is not None:
        yield http
        return
    async with new_client() as client:
        yield client


def _retryable(exc: BaseException) -> bool:
    if isinstance(exc, httpx.TransportError):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in RETRY_STATUSES
    return False


_retry = retry(
    retry=retry_if_exception(_retryable),
    stop=stop_after_attempt(2),
    wait=wait_fixed(0.5),
    reraise=True,
)


@_retry
async def get_json(http: httpx.AsyncClient, url: str, params: Optional[dict] = None) -> Any:
    response = await http.get(url, params=params)
    response.raise_for_status()
    return response.json()


@_retry
async def post_json(http: httpx.AsyncClient, url: str, payload: Any) -> Any:
    """POST that only reads. Used for CLOB's /books batch and nothing else."""
    response = await http.post(url, json=payload)
    response.raise_for_status()
    return response.json()
