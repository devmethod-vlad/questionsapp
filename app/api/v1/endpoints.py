"""Versioned API endpoints for FastAPI migration with contract compatibility."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, File, Form, Query, UploadFile
from fastapi.responses import PlainTextResponse

from app.responses.builders import error, ok, paginated_questions
from app.schemas.payloads import BotExcelPayload, QuestionsListPayload, ServicePayload, SpaceRolesPayload, StatisticPayload
from app.services.legacy_bridge import FileCompat, LegacyServiceAdapter

router = APIRouter()


@router.get("/test/")
def test_endpoint() -> PlainTextResponse:
    return PlainTextResponse("Test success!!!")


@router.get("/questions_api/")
def questions_api(
    publicorder: str = Query(default="0"),
    page_count: str = Query(default="100"),
    page: str = Query(default="1"),
):
    try:
        parsed_page_count = int(page_count)
        if parsed_page_count < 1:
            parsed_page_count = 100
        if parsed_page_count > 500:
            parsed_page_count = 500

        parsed_page = int(page)
        if parsed_page < 1:
            parsed_page = 1
    except ValueError:
        return error("Invalid pagination parameters; must be integers.", status_code=400)

    records, total_count = LegacyServiceAdapter.get_questions_api(
        page=parsed_page,
        page_count=parsed_page_count,
        public_only=(publicorder == "1"),
    )
    return paginated_questions(count=total_count, page_count=len(records), page=parsed_page, data=records)


@router.post("/questionslist/")
def questions_list(payload: QuestionsListPayload):
    response, status_code = LegacyServiceAdapter.form_questions_list(payload.model_dump())
    return ok(response, status_code=status_code)


@router.post("/spaceandroles/")
def space_roles(payload: SpaceRolesPayload):
    if not payload.action:
        return error("WARN: No action param")
    if payload.action != "getrolesbyspace":
        return error("WARN: No valid action param")

    response, status_code = LegacyServiceAdapter.get_roles(payload.model_dump())
    return ok(response, status_code=status_code)


@router.post("/saveorupdate/")
async def save_or_update(
    action: Annotated[str | None, Form()] = None,
    spacekey: Annotated[str | None, Form()] = None,
    orderid: Annotated[str | None, Form()] = None,
    userid: Annotated[str | None, Form()] = None,
    unionroleid: Annotated[str | None, Form()] = None,
    question_text: Annotated[str | None, Form()] = None,
    answer_text: Annotated[str | None, Form()] = None,
    publicorder: Annotated[str | None, Form()] = None,
    fastformflag: Annotated[str | None, Form()] = None,
    userfingerprintid: Annotated[str | None, Form()] = None,
    fio: Annotated[str | None, Form()] = None,
    login: Annotated[str | None, Form()] = None,
    muname: Annotated[str | None, Form()] = None,
    phone: Annotated[str | None, Form()] = None,
    mail: Annotated[str | None, Form()] = None,
    isfeedback: Annotated[str | None, Form()] = None,
    question_files: list[UploadFile] = File(default_factory=list, alias="question_files[]"),
    answer_files: list[UploadFile] = File(default_factory=list, alias="answer_files[]"),
):
    if not action:
        return error("WARN: No action param")

    payload = {
        "spacekey": spacekey,
        "orderid": orderid,
        "userid": userid,
        "unionroleid": unionroleid,
        "question_text": question_text,
        "answer_text": answer_text,
        "question_files": [FileCompat(f) for f in question_files],
        "answer_files": [FileCompat(f) for f in answer_files],
        "publicorder": publicorder,
        "fastformflag": fastformflag,
        "userfingerprintid": userfingerprintid,
        "fio": fio,
        "login": login,
        "muname": muname,
        "phone": phone,
        "mail": mail,
        "isfeedback": isfeedback,
    }

    response, status_code = LegacyServiceAdapter.save_or_update(action, payload)
    return ok(response, status_code=status_code)


@router.post("/service/")
def service(payload: ServicePayload):
    if not payload.action:
        return error("WARN: No action param")
    response, status_code = LegacyServiceAdapter.service_action(payload.model_dump(exclude_none=False))
    return ok(response, status_code=status_code)


@router.post("/statistic/")
def statistic(payload: StatisticPayload):
    if not payload.action:
        return error("WARN: No action param")
    if payload.action != "getbotstat":
        return error("WARN: No valid action param")
    if not payload.botstatskind or payload.botimeperiod not in (7, 30):
        return error("WARN: No params")

    response, status_code = LegacyServiceAdapter.statistic(payload.model_dump())
    return ok(response, status_code=status_code)


@router.post("/botexcel/")
def botexcel(payload: BotExcelPayload):
    if not payload.action or payload.chatid in (None, ""):
        return error("WARN: No params")

    response, status_code = LegacyServiceAdapter.botexcel(payload.model_dump())
    return ok(response, status_code=status_code)
