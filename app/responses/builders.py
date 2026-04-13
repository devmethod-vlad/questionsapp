"""Compatibility response builders.

Centralize envelopes so migrated handlers preserve legacy payload shapes.
"""

from __future__ import annotations

from typing import Any

from fastapi.responses import JSONResponse


JSON_UTF8 = "application/json; charset=utf-8"


def ok(payload: dict[str, Any] | None = None, status_code: int = 200) -> JSONResponse:
    body = payload if payload is not None else {"status": "ok"}
    return JSONResponse(content=body, status_code=status_code, media_type=JSON_UTF8)


def error(message: str, status_code: int = 200) -> JSONResponse:
    body = {"status": "error", "error_mess": message}
    return JSONResponse(content=body, status_code=status_code, media_type=JSON_UTF8)


def paginated_questions(*, count: int, page_count: int, page: int, data: list[dict[str, Any]]) -> JSONResponse:
    body = {
        "count": count,
        "page_count": page_count,
        "page": page,
        "data": data,
    }
    return JSONResponse(content=body, status_code=200, media_type=JSON_UTF8)
