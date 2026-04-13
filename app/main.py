"""FastAPI application entrypoint.

Implements migration steps:
- skeleton and modular layout
- infra middleware and healthcheck
- centralized error handling
- compatibility-first API routing
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import RequestIDMiddleware, RequestLoggingMiddleware
from app.responses.builders import ok

configure_logging()

app = FastAPI(title=settings.app_name, version=settings.app_version)
register_exception_handlers(app)

if settings.enable_cors:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )

app.add_middleware(RequestIDMiddleware)
app.add_middleware(RequestLoggingMiddleware)


@app.get("/health")
def healthcheck():
    return ok({"status": "ok"})


app.include_router(api_router, prefix=settings.api_prefix)
