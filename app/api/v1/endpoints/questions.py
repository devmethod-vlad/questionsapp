"""Question API endpoints migrated to FastAPI with legacy-compatible contracts."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile

from app.repositories.legacy_session import LegacySessionContext, get_legacy_session_context
from app.responses.builders import error, ok, paginated_questions
from app.schemas.payloads import (
    BotExcelPayload,
    QuestionsAPIQuery,
    QuestionsListPayload,
    SaveOrUpdatePayload,
    ServicePayload,
    SpaceRolesPayload,
    StatisticPayload,
)
from app.services.admin_service import AdminService
from app.services.questions_service import QuestionsService

router = APIRouter()


@router.get("/questions_api/")
def questions_api(
    query: Annotated[QuestionsAPIQuery, Depends()],
    _: Annotated[LegacySessionContext, Depends(get_legacy_session_context)],
):
    try:
        parsed_page_count = int(query.page_count)
        if parsed_page_count < 1:
            parsed_page_count = 100
        if parsed_page_count > 500:
            parsed_page_count = 500

        parsed_page = int(query.page)
        if parsed_page < 1:
            parsed_page = 1
    except ValueError:
        return error("Invalid pagination parameters; must be integers.", status_code=400)

    records, total_count = QuestionsService.get_public_questions(
        page=parsed_page,
        page_count=parsed_page_count,
        public_only=(query.publicorder == "1"),
    )
    return paginated_questions(count=total_count, page_count=len(records), page=parsed_page, data=records)


@router.post("/questionslist/")
def questions_list(
    payload: QuestionsListPayload,
    _: Annotated[LegacySessionContext, Depends(get_legacy_session_context)],
):
    response, status_code = QuestionsService.get_questions_list(payload.model_dump())
    return ok(response, status_code=status_code)


@router.post("/spaceandroles/")
def space_roles(
    payload: SpaceRolesPayload,
    _: Annotated[LegacySessionContext, Depends(get_legacy_session_context)],
):
    if not payload.action:
        return error("WARN: No action param")
    if payload.action != "getrolesbyspace":
        return error("WARN: No valid action param")

    response, status_code = AdminService.get_space_roles(payload.model_dump())
    return ok(response, status_code=status_code)


@router.post("/saveorupdate/")
async def save_or_update(
    form_data: Annotated[SaveOrUpdatePayload, Depends(SaveOrUpdatePayload.from_form)],
    _: Annotated[LegacySessionContext, Depends(get_legacy_session_context)],
    question_files: list[UploadFile] = File(default_factory=list, alias="question_files[]"),
    answer_files: list[UploadFile] = File(default_factory=list, alias="answer_files[]"),
):
    if not form_data.action:
        return error("WARN: No action param")

    response, status_code = QuestionsService.save_or_update(
        action=form_data.action,
        payload=form_data.model_dump(),
        question_files=question_files,
        answer_files=answer_files,
    )
    return ok(response, status_code=status_code)


@router.post("/service/")
def service(
    payload: ServicePayload,
    _: Annotated[LegacySessionContext, Depends(get_legacy_session_context)],
):
    if not payload.action:
        return error("WARN: No action param")
    response, status_code = AdminService.execute_service_action(payload.model_dump(exclude_none=False))
    return ok(response, status_code=status_code)


@router.post("/statistic/")
def statistic(
    payload: StatisticPayload,
    _: Annotated[LegacySessionContext, Depends(get_legacy_session_context)],
):
    if not payload.action:
        return error("WARN: No action param")
    if payload.action != "getbotstat":
        return error("WARN: No valid action param")
    if not payload.botstatskind or payload.botimeperiod not in (7, 30):
        return error("WARN: No params")

    response, status_code = AdminService.get_statistics(payload.model_dump())
    return ok(response, status_code=status_code)


@router.post("/botexcel/")
def botexcel(
    payload: BotExcelPayload,
    _: Annotated[LegacySessionContext, Depends(get_legacy_session_context)],
):
    if not payload.action or payload.chatid in (None, ""):
        return error("WARN: No params")

    response, status_code = AdminService.build_bot_excel(payload.model_dump())
    return ok(response, status_code=status_code)
