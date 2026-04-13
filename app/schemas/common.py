"""Shared Pydantic schemas and enums for migrated endpoints."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class LegacyBaseModel(BaseModel):
    """Base model with permissive extra handling for backward compatibility."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class LegacyStatusResponse(LegacyBaseModel):
    status: str
    error_mess: str | None = None


class QuestionsAPIResponse(LegacyBaseModel):
    count: int
    page_count: int
    page: int
    data: list[dict[str, Any]]
