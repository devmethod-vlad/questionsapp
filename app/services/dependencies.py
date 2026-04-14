"""Dependency providers for FastAPI service layer."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.db.session import RequestSessionContext, get_request_session_context
from app.repositories.questions_list_repository import SqlAlchemyQuestionsListRepository
from app.repositories.questions_repository import SqlAlchemyQuestionsReadRepository
from app.repositories.web_repository import SqlAlchemyWebRepository
from app.services.questions_service import QuestionsService
from app.services.web_service import WebService


def get_questions_service(
    session_context: Annotated[RequestSessionContext, Depends(get_request_session_context)],
) -> QuestionsService:
    """Build question service with repository dependencies for current request."""

    read_repository = SqlAlchemyQuestionsReadRepository(session_context.session)
    questions_list_repository = SqlAlchemyQuestionsListRepository(
        session=session_context.session,
        engine=session_context.session.get_bind(),
    )
    return QuestionsService(
        questions_read_repository=read_repository,
        questions_list_repository=questions_list_repository,
    )


def get_web_service(
    session_context: Annotated[RequestSessionContext, Depends(get_request_session_context)],
) -> WebService:
    """Build web service with repository dependencies for current request."""

    repository = SqlAlchemyWebRepository(session=session_context.session)
    return WebService(repository=repository)
