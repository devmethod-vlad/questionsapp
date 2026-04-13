"""Custom middleware for request id propagation and structured request logging."""

from __future__ import annotations

import logging
import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach request id to request.state and response headers."""

    def __init__(self, app, header_name: str = "X-Request-ID"):
        super().__init__(app)
        self.header_name = header_name

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get(self.header_name, str(uuid.uuid4()))
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers[self.header_name] = request_id
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log request/response envelope with latency for baseline comparison."""

    def __init__(self, app):
        super().__init__(app)
        self.logger = logging.getLogger("questionsapp.fastapi.request")

    async def dispatch(self, request: Request, call_next):
        started = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        self.logger.info(
            "request_completed",
            extra={
                "request_id": getattr(request.state, "request_id", ""),
            },
        )
        self.logger.info(
            f"method={request.method} path={request.url.path} status={response.status_code} elapsed_ms={elapsed_ms}"
        )
        return response
