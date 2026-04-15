"""Question API endpoints migrated to FastAPI with legacy-compatible contracts."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, File, Query, UploadFile
from fastapi.responses import Response

from app.core.rate_limit import enforce_questions_api_rate_limit
from app.db.session import RequestSessionContext, get_request_session_context
from app.responses.builders import error, ok, paginated_questions
from app.schemas.payloads import SaveOrUpdatePayload
from app.schemas.responses import LegacyErrorResponse, QuestionsAPISuccessResponse
from app.services.admin_service import AdminService
from app.services.dependencies import get_questions_service
from app.services.questions_service import QuestionsService

router = APIRouter()


@router.get(
    "/questions_api/",
    dependencies=[Depends(enforce_questions_api_rate_limit)],
    response_model=QuestionsAPISuccessResponse,
    responses={
        400: {"model": LegacyErrorResponse, "description": "Legacy validation error envelope"},
        429: {"model": LegacyErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": LegacyErrorResponse, "description": "Internal server error envelope"},
    },
)
def questions_api(
    questions_service: Annotated[QuestionsService, Depends(get_questions_service)],
    publicorder: str = Query(default="0"),
    page_count: str = Query(default="100"),
    page: str = Query(default="1"),
):
    try:
        records, total_count = questions_service.get_public_questions(
            page=page,
            page_count=page_count,
            public_only=(publicorder == "1"),
        )
    except ValueError:
        return error("Invalid pagination parameters; must be integers.", status_code=400)
    except Exception:
        return error("Internal server error while fetching data.", status_code=500)

    parsed_page = max(1, int(page))
    return paginated_questions(count=total_count, page_count=len(records), page=parsed_page, data=records)


@router.post("/questionslist/")
def questions_list(
    questions_service: Annotated[QuestionsService, Depends(get_questions_service)],
    _: Annotated[RequestSessionContext, Depends(get_request_session_context)],
    payload: dict[str, Any] | None = Body(default=None),
):
    request_payload = payload if isinstance(payload, dict) else {}
    response, status_code = questions_service.get_questions_list(request_payload)
    return ok(response, status_code=status_code)


@router.post("/spaceandroles/")
def space_roles(
    session_context: Annotated[RequestSessionContext, Depends(get_request_session_context)],
    payload: dict[str, Any] | None = Body(default=None),
):
    request_payload = payload if isinstance(payload, dict) else {}
    action = request_payload.get("action")
    if not action:
        return error("WARN: No action param")
    if action != "getrolesbyspace":
        return error("WARN: No valid action param")

    response, status_code = AdminService.get_space_roles(request_payload, session=session_context.session)
    return ok(response, status_code=status_code)


@router.post("/saveorupdate/")
async def save_or_update(
    form_data: Annotated[SaveOrUpdatePayload, Depends(SaveOrUpdatePayload.from_form)],
    session_context: Annotated[RequestSessionContext, Depends(get_request_session_context)],
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
        session=session_context.session,
    )
    return ok(response, status_code=status_code)


@router.post("/service/")
def service(
    session_context: Annotated[RequestSessionContext, Depends(get_request_session_context)],
    payload: dict[str, Any] | None = Body(default=None),
):
    request_payload = payload if isinstance(payload, dict) else {}
    if not request_payload.get("action"):
        return error("WARN: No action param")
    response, status_code = AdminService.execute_service_action(
        request_payload,
        session=session_context.session,
    )
    return ok(response, status_code=status_code)


@router.post("/statistic/")
def statistic(
    session_context: Annotated[RequestSessionContext, Depends(get_request_session_context)],
    payload: dict[str, Any] | None = Body(default=None),
):
    request_payload = payload if isinstance(payload, dict) else {}
    action = request_payload.get("action")
    botstatskind = request_payload.get("botstatskind")
    botimeperiod = request_payload.get("botimeperiod")

    if not action:
        return error("WARN: No action param")
    if action != "getbotstat":
        return error("WARN: No valid action param")
    if not botstatskind or botimeperiod not in (7, 30):
        return error("WARN: No params")

    response = AdminService.get_statistics(request_payload, session=session_context.session)
    if isinstance(response, Response):
        return response

    payload_body, status_code = response
    return ok(payload_body, status_code=status_code)


@router.post("/botexcel/")
def botexcel(
    _: Annotated[RequestSessionContext, Depends(get_request_session_context)],
    payload: dict[str, Any] | None = Body(default=None),
):
    request_payload = payload if isinstance(payload, dict) else {}
    if not request_payload.get("action") or request_payload.get("chatid") in (None, ""):
        return error("WARN: No params")

    response, status_code = AdminService.build_bot_excel(request_payload)
    return ok(response, status_code=status_code)
