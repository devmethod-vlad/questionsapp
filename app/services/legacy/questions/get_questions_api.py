"""Legacy-compatible questions API read helper.

The helper is shared by legacy Flask routes and native FastAPI services.
It keeps pagination normalization and payload shape identical while routing
all reads through the repository abstraction.
"""

from __future__ import annotations

from app.core.runtime_config import get_url_prefix
from app.repositories.questions_repository import QuestionsReadRepository, SqlAlchemyQuestionsReadRepository


def get_questions_api_data(
    *,
    page: int = 1,
    page_count: int = 100,
    public_only: bool = True,
    repository: QuestionsReadRepository | None = None,
) -> tuple[list[dict], int]:
    """Return paginated question feed and total count.

    Args:
        page: Requested page number.
        page_count: Requested records per page.
        public_only: Whether only public questions should be returned.
        repository: Optional repository override (used by FastAPI DI).
    """

    if repository is None:
        from database import db

        repository = SqlAlchemyQuestionsReadRepository(db.session)

    normalized_page, normalized_page_count = _normalize_pagination(page=page, page_count=page_count)
    return repository.get_public_questions(
        page=normalized_page,
        page_count=normalized_page_count,
        public_only=public_only,
        url_prefix=get_url_prefix(),
    )


def _normalize_pagination(*, page: int, page_count: int) -> tuple[int, int]:
    """Normalize pagination values with legacy-compatible defaults."""

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

    return page, page_count
