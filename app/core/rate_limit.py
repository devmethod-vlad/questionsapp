"""Lightweight per-endpoint rate limiting helpers."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from threading import Lock
from time import monotonic

from fastapi import HTTPException, Request


@dataclass(slots=True)
class SlidingWindowRateLimiter:
    """In-memory sliding-window limiter keyed by arbitrary client identifier."""

    limit: int
    period_seconds: int
    _events: dict[str, deque[float]] = field(default_factory=lambda: defaultdict(deque))
    _lock: Lock = field(default_factory=Lock)

    def allow(self, key: str) -> bool:
        now = monotonic()
        period_start = now - self.period_seconds

        with self._lock:
            hits = self._events[key]
            while hits and hits[0] <= period_start:
                hits.popleft()
            if len(hits) >= self.limit:
                return False
            hits.append(now)
            return True

    def reset(self) -> None:
        with self._lock:
            self._events.clear()


questions_api_limiter = SlidingWindowRateLimiter(limit=60, period_seconds=60)


def _client_identifier(request: Request) -> str:
    """Best-effort client ID that keeps reverse proxy compatibility."""
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        # First hop is the original client in the common XFF format.
        return forwarded_for.split(",", maxsplit=1)[0].strip()

    if request.client and request.client.host:
        return request.client.host

    return "unknown-client"


def enforce_questions_api_rate_limit(request: Request) -> None:
    client_key = _client_identifier(request)
    if questions_api_limiter.allow(client_key):
        return

    raise HTTPException(status_code=429, detail="60 per minute")
