"""Compatibility wrappers for legacy `questionslist` imports.

The active FastAPI runtime now uses native service/repository layers under
`app/services` and `app/repositories`. These wrappers keep import stability for
remaining legacy call-sites during migration.
"""

from __future__ import annotations

from typing import Any

from app.db.legacy_db import db

from app.repositories.questions_list_repository import SqlAlchemyQuestionsListRepository
from app.services.questions_list_service import QuestionsListService


def _service() -> QuestionsListService:
    repository = SqlAlchemyQuestionsListRepository(session=db.session, engine=db.session.get_bind())
    return QuestionsListService(repository=repository)


def find_question_in_list(params: dict[str, Any]):
    """Legacy-compatible wrapper around native `find_question_in_list` flow."""

    return _service().find_question_in_list(params)


def form_questions_list(params: dict[str, Any]):
    """Legacy-compatible wrapper around native `questionslist` flow."""

    return _service().form_questions_list(params)
