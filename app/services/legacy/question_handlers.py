"""Adapters for question-domain endpoints.

These adapters isolate endpoint orchestration from the low-level legacy bridge
and keep migration 4.2 explicit: route translation and legacy service reuse
remain separate concerns.
"""

from __future__ import annotations

from typing import Any

from app.services.legacy_bridge import FileCompat, LegacyServiceAdapter


class LegacyQuestionHandlers:
    """Facade used by FastAPI routers for question domain actions."""

    @staticmethod
    def questions_api(*, page: int, page_count: int, public_only: bool):
        return LegacyServiceAdapter.get_questions_api(page=page, page_count=page_count, public_only=public_only)

    @staticmethod
    def questions_list(payload: dict[str, Any]):
        return LegacyServiceAdapter.form_questions_list(payload)

    @staticmethod
    def save_or_update(action: str, payload: dict[str, Any], question_files: list[Any], answer_files: list[Any]):
        payload = dict(payload)
        payload.update(
            {
                "question_files": [FileCompat(f) for f in question_files],
                "answer_files": [FileCompat(f) for f in answer_files],
            }
        )
        return LegacyServiceAdapter.save_or_update(action, payload)
