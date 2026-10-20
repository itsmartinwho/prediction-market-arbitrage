"""A small in-memory cache: a time to live, one computation per key at a time,
and the last good value when a refresh fails.

It lives in one process. On Vercel, Fluid compute keeps a function instance
warm between requests, so the cache saves repeat work there; a cold instance
starts empty, and Vercel's CDN (see the Cache-Control middleware in main.py)
is what spares most requests from reaching a function at all.
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, Generic, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

# How long a value may still be served after its refresh failed.
STALE_LIMIT_SECONDS = 600


@dataclass(frozen=True)
class Entry(Generic[T]):
    value: T
    stored_at: float  # time.time() when it was computed


class TTLCache:
    def __init__(self, clock: Callable[[], float] = time.time, max_entries: int = 256):
        self._clock = clock
        self._max_entries = max_entries
        self._entries: Dict[str, Entry] = {}
        self._inflight: Dict[str, "asyncio.Task[Entry]"] = {}

    def peek(self, key: str) -> Optional[Entry]:
        return self._entries.get(key)

    def age(self, key: str) -> Optional[float]:
        entry = self._entries.get(key)
        return None if entry is None else self._clock() - entry.stored_at

    def clear(self) -> None:
        self._entries.clear()
        self._inflight.clear()

    async def get(self, key: str, ttl: float, compute: Callable[[], Awaitable[T]]) -> Entry[T]:
        """The cached entry if younger than `ttl`, else a fresh one.

        Concurrent callers for the same key share one computation. If it fails
        and an older entry exists (up to STALE_LIMIT_SECONDS old), that entry
        is returned instead of the error.
        """
        entry = self._entries.get(key)
        if entry is not None and self._clock() - entry.stored_at < ttl:
            return entry
        try:
            return await self.refresh(key, compute)
        except Exception as e:
            if entry is not None and self._clock() - entry.stored_at < STALE_LIMIT_SECONDS:
                logger.warning(f"Refreshing {key} failed ({e}); serving the previous value")
                return entry
            raise

    async def refresh(self, key: str, compute: Callable[[], Awaitable[T]]) -> Entry[T]:
        """Compute now, or join the computation already running for `key`."""
        loop = asyncio.get_running_loop()
        task = self._inflight.get(key)
        if task is None or task.done() or task.get_loop() is not loop:
            task = loop.create_task(self._run(key, compute))
            task.add_done_callback(_consume_exception)
            self._inflight[key] = task
        # shield: a caller that goes away does not cancel the shared work
        return await asyncio.shield(task)

    async def _run(self, key: str, compute: Callable[[], Awaitable[Any]]) -> Entry:
        try:
            entry = Entry(await compute(), self._clock())
            self._entries[key] = entry
            while len(self._entries) > self._max_entries:  # searches are open-ended
                oldest = min(self._entries, key=lambda k: self._entries[k].stored_at)
                del self._entries[oldest]
            return entry
        finally:
            if self._inflight.get(key) is asyncio.current_task():
                del self._inflight[key]


def _consume_exception(task: "asyncio.Task") -> None:
    # Mark a failure as seen even if every waiter has gone, so asyncio does not
    # log "Task exception was never retrieved".
    if not task.cancelled():
        task.exception()


_shared = TTLCache()


def shared_cache() -> TTLCache:
    """The process-wide cache every endpoint uses."""
    return _shared
