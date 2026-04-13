"""Request payload schemas preserving current API contracts."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from app.schemas.common import LegacyBaseModel


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
