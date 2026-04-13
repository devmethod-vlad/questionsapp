"""Legacy-compatible response schemas.

Migration step 3.2:
- response contracts are explicitly documented with Pydantic models;
- handlers still return JSON via response builders to preserve exact payloads.
"""

from __future__ import annotations

from typing import Any

from app.schemas.common import LegacyBaseModel


class LegacyErrorResponse(LegacyBaseModel):
    status: str = "error"
    error_mess: str


class LegacyOkStatusResponse(LegacyBaseModel):
    status: str = "ok"


class QuestionsAPISuccessResponse(LegacyBaseModel):
    count: int
    page_count: int
    page: int
    data: list[dict[str, Any]]

