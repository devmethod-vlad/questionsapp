"""Minimal in-memory rate limiting helpers for selected legacy-compatible endpoints."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from threading import Lock
import time

from fastapi import HTTPException, Request


@dataclass(frozen=True)
class RateLimitRule:
    requests: int
    period_seconds: int


class InMemoryRateLimiter:
    """Simple fixed-window limiter keyed by `<route>::<client>` in process memory."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._history: dict[str, deque[float]] = defaultdict(deque)

    def hit(self, *, key: str, rule: RateLimitRule) -> bool:
        now = time.time()
        window_start = now - rule.period_seconds
        with self._lock:
            history = self._history[key]
            while history and history[0] <= window_start:
                history.popleft()
            if len(history) >= rule.requests:
                return False
            history.append(now)
            return True

    def reset(self) -> None:
        with self._lock:
            self._history.clear()


questions_api_rate_limit = InMemoryRateLimiter()
QUESTIONS_API_RULE = RateLimitRule(requests=60, period_seconds=60)


def _client_address(request: Request) -> str:
    """Match Flask-Limiter default key_func=get_remote_address behaviour as closely as possible."""

    if request.client and request.client.host:
        return request.client.host
    return "127.0.0.1"


def enforce_questions_api_rate_limit(request: Request) -> None:
    """Apply legacy-compatible 60 req/min limit for GET /questions_api/."""

    client_key = _client_address(request)
    key = f"questions_api::{client_key}"
    if not questions_api_rate_limit.hit(key=key, rule=QUESTIONS_API_RULE):
        raise HTTPException(status_code=429, detail="Too Many Requests")
