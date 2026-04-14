"""Question-domain application services.

This module is the stable service layer used by FastAPI routers.
It hides legacy implementation details while preserving the existing
external API contract.
"""

from __future__ import annotations

from typing import Any

from app.core.runtime_config import get_url_prefix
from app.repositories.questions_repository import QuestionsReadRepository
from app.services.legacy_bridge import FileCompat, LegacyServiceAdapter


class QuestionsService:
    """Application service for question-related operations."""

    def __init__(self, *, questions_read_repository: QuestionsReadRepository):
        self._questions_read_repository = questions_read_repository

    def get_public_questions(self, *, page: int, page_count: int, public_only: bool):
        """Return public questions through native repository abstraction.

        Pagination normalization intentionally lives in the service layer to keep
        endpoint handlers thin and to preserve legacy-compatible defaults.
        """

        normalized_page, normalized_page_count = self._normalize_public_api_pagination(
            page=page,
            page_count=page_count,
        )

        return self._questions_read_repository.get_public_questions(
            page=normalized_page,
            page_count=normalized_page_count,
            public_only=public_only,
            url_prefix=get_url_prefix(),
        )

    @staticmethod
    def _normalize_public_api_pagination(*, page: int, page_count: int) -> tuple[int, int]:
        """Validate and normalize `questions_api` pagination parameters.

        Raises:
            ValueError: if either value cannot be converted to integer.
        """

        parsed_page_count = int(page_count)
        if parsed_page_count < 1:
            parsed_page_count = 100
        if parsed_page_count > 500:
            parsed_page_count = 500

        parsed_page = int(page)
        if parsed_page < 1:
            parsed_page = 1

        return parsed_page, parsed_page_count

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
