"""Request payload schemas preserving current API contracts.

Migration step 3.1:
- explicit request schemas for each endpoint;
- permissive parsing (`extra="allow"`) to avoid breaking legacy clients;
- alias mapping support where field names can differ from Python identifiers.
"""

from __future__ import annotations

from typing import Literal

from fastapi import Form
from pydantic import Field

from app.schemas.common import LegacyBaseModel


class QuestionsAPIQuery(LegacyBaseModel):
    """Query schema for `/questions_api/` with legacy defaults."""

    publicorder: str = "0"
    page_count: str = "100"
    page: str = "1"


class QuestionsListPayload(LegacyBaseModel):
    userid: int | None = None
    roleid: int | None = None
    orderid: int | None = None
    spaceid: int | None = None
    statusid: int | None = None
    perpagecount: int | None = None
    activepage: int | None = None
    datesort: str | None = None
    searchinput: str | None = None
    enablesearch: int | None = None
    isfeedback: int | None = None
    showonlypublic: int | None = None
    usertoken: str | None = None
    forsynchroflag: int | None = None
    findquestioninlist: int | bool | None = None


class SpaceRolesPayload(LegacyBaseModel):
    action: str | None = None
    spaceid: int | None = None
    roleid: int | None = None
    userid: int | None = None


class ServicePayload(LegacyBaseModel):
    action: str | None = None
    orderid: int | None = None
    userid: int | None = None
    attachid: int | None = None
    execute_action: str | None = None
    publicflag: int | None = None
    attach_target: str | None = None
    edulogin: str | None = None
    adminlogin: str | None = None
    adminpass: str | None = None
    tokenlifetime: int | None = None
    botname: str | None = None
    uploadsize: int | None = None


class StatisticPayload(LegacyBaseModel):
    action: str | None = None
    botstatskind: Literal["newusers", "phrazestats", "phrazesperday"] | None = None
    botimeperiod: int | None = Field(default=None, description="Supported values: 7 or 30")
    botdownloadflag: int | None = None


class BotExcelPayload(LegacyBaseModel):
    action: Literal["getfollowersexcel", "getsuppinfo"] | None = None
    chatid: int | str | None = None


class SaveOrUpdatePayload(LegacyBaseModel):
    """Form schema for `/saveorupdate/` text fields.

    File fields are processed separately as raw multipart file lists to keep
    compatibility with the legacy `question_files[]`/`answer_files[]` names.
    """

    action: str | None = None
    spacekey: str | None = None
    orderid: str | None = None
    userid: str | None = None
    unionroleid: str | None = None
    question_text: str | None = None
    answer_text: str | None = None
    publicorder: str | None = None
    fastformflag: str | None = None
    userfingerprintid: str | None = None
    fio: str | None = None
    login: str | None = None
    muname: str | None = None
    phone: str | None = None
    mail: str | None = None
    isfeedback: str | None = None

    @classmethod
    def from_form(
        cls,
        action: str | None = Form(default=None),
        spacekey: str | None = Form(default=None),
        orderid: str | None = Form(default=None),
        userid: str | None = Form(default=None),
        unionroleid: str | None = Form(default=None),
        question_text: str | None = Form(default=None),
        answer_text: str | None = Form(default=None),
        publicorder: str | None = Form(default=None),
        fastformflag: str | None = Form(default=None),
        userfingerprintid: str | None = Form(default=None),
        fio: str | None = Form(default=None),
        login: str | None = Form(default=None),
        muname: str | None = Form(default=None),
        phone: str | None = Form(default=None),
        mail: str | None = Form(default=None),
        isfeedback: str | None = Form(default=None),
    ) -> "SaveOrUpdatePayload":
        """Build model from multipart/form-data values."""

        return cls(
            action=action,
            spacekey=spacekey,
            orderid=orderid,
            userid=userid,
            unionroleid=unionroleid,
            question_text=question_text,
            answer_text=answer_text,
            publicorder=publicorder,
            fastformflag=fastformflag,
            userfingerprintid=userfingerprintid,
            fio=fio,
            login=login,
            muname=muname,
            phone=phone,
            mail=mail,
            isfeedback=isfeedback,
        )
