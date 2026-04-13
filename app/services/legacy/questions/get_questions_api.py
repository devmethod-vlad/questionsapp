"""Legacy-compatible wrapper for question API feed retrieval.

SQL moved to repository layer (step 3.2 cleanup) while preserving function
signature and return format expected by legacy bridge.
"""

from __future__ import annotations

from flask import current_app

from app.repositories.questions_repository import QuestionsReadRepository


def get_questions_api_data(
    *,
    page: int = 1,
    page_count: int = 100,
    public_only: bool = True,
    repository: QuestionsReadRepository,
) -> tuple[list[dict], int]:
    """Return paginated questions and count using repository abstraction."""

    try:
        page_count = int(page_count)
    except Exception:
        page_count = 100
    page_count = max(1, min(page_count, 500))

    try:
        page = int(page)
    except Exception:
        page = 1
    page = max(1, page)

    return repository.get_public_questions(
        page=page,
        page_count=page_count,
        public_only=public_only,
        url_prefix=current_app.config.get("URL_PREFIX", ""),
    )
