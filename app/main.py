"""FastAPI application entrypoint.

Implements migration steps:
- skeleton and modular layout
- infra middleware and healthcheck
- centralized error handling
- compatibility-first API routing
"""

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.settings import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import RequestIDMiddleware, RequestLoggingMiddleware
from app.responses.builders import ok

configure_logging()
settings = get_settings()

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


def custom_openapi() -> dict:
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
        description=app.description,
    )

    for path_item in openapi_schema.get("paths", {}).values():
        for operation in path_item.values():
            if not isinstance(operation, dict):
                continue

            responses = operation.get("responses", {})
            if "422" in responses:
                responses.pop("422")
                responses.setdefault(
                    "400",
                    {
                        "description": "Validation error (legacy envelope)",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/LegacyErrorResponse"},
                            }
                        },
                    },
                )

    schemas = openapi_schema.get("components", {}).get("schemas", {})
    schemas.pop("HTTPValidationError", None)
    schemas.pop("ValidationError", None)

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.get("/health")
def healthcheck():
    return ok({"status": "ok"})


app.include_router(api_router, prefix=settings.api_prefix)
