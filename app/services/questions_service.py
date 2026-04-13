"""Question-domain application services.

This module is the stable service layer used by FastAPI routers.
It hides the legacy implementation details while preserving the
existing external API contract.
"""

from __future__ import annotations

from typing import Any

from app.services.legacy_bridge import FileCompat, LegacyServiceAdapter


class QuestionsService:
    """Application service for question-related operations."""

    @staticmethod
    def get_public_questions(*, page: int, page_count: int, public_only: bool):
        return LegacyServiceAdapter.get_questions_api(
            page=page,
            page_count=page_count,
            public_only=public_only,
        )

    @staticmethod
    def get_questions_list(payload: dict[str, Any]):
        return LegacyServiceAdapter.form_questions_list(payload)

    @staticmethod
    def save_or_update(action: str, payload: dict[str, Any], question_files: list[Any], answer_files: list[Any]):
        wrapped_payload = dict(payload)
        wrapped_payload.update(
            {
                "question_files": [FileCompat(file_obj) for file_obj in question_files],
                "answer_files": [FileCompat(file_obj) for file_obj in answer_files],
            }
        )
        return LegacyServiceAdapter.save_or_update(action, wrapped_payload)
