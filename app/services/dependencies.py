"""Dependency providers for FastAPI service layer."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.db.session import RequestSessionContext, get_request_session_context
from app.repositories.questions_repository import SqlAlchemyQuestionsReadRepository
from app.services.questions_service import QuestionsService


def get_questions_service(
    session_context: Annotated[RequestSessionContext, Depends(get_request_session_context)],
) -> QuestionsService:
    """Build question service with repository dependencies for current request."""

    repository = SqlAlchemyQuestionsReadRepository(session_context.session)
    return QuestionsService(questions_read_repository=repository)
