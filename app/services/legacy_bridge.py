"""Bridge layer that allows FastAPI handlers to call legacy Flask services.

This keeps business logic untouched during migration while routing and
validation are moved to FastAPI.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

from fastapi import UploadFile

import questionsapp
from questionsapp import create_app
from questionsapp.services.appconfig.getappconfig import get_appconfig_info
from questionsapp.services.appconfig.updateconfig import update_app_config
from questionsapp.services.attachments.changeatttachpublicity import change_attach_publicity
from questionsapp.services.attachments.deleteattachment import delete_attachment
from questionsapp.services.auxillary.getrolesbyspace import get_roles_by_space
from questionsapp.services.auxillary.telegram import _tg_post
from questionsapp.services.questions.execaction import exec_action
from questionsapp.services.questions.get_questions_api import get_questions_api_data
from questionsapp.services.questions.saveanonymquestion import save_anonym_question
from questionsapp.services.questions.savecombine import save_combine
from questionsapp.services.questions.savequestion import save_question
from questionsapp.services.questionslist.formquestionslist import find_question_in_list, form_questions_list
from questionsapp.services.roles.changeadminpass import change_admin_pass
from questionsapp.services.roles.createnewadmin import create_new_admin
from questionsapp.services.roles.enteradmin import enter_admin
from questionsapp.services.roles.exitadmin import exit_admin
from questionsapp.services.stats.bot.getnewuser import get_newuser_stat
from questionsapp.services.stats.bot.getphrazestat import get_phraze_stat
from questionsapp.services.stats.bot.phrazesperdaystat import get_perdayphrazes_stat

_legacy_flask_app = None


def get_legacy_flask_app():
    """Lazily construct Flask app required by legacy business services.

    Lazy initialization keeps FastAPI-only operations (e.g. OpenAPI generation)
    independent from runtime-only Flask env requirements.
    """

    global _legacy_flask_app
    if _legacy_flask_app is None:
        _legacy_flask_app = create_app(celery=questionsapp.celery)
    return _legacy_flask_app


@contextmanager
def flask_context() -> Iterator[None]:
    with get_legacy_flask_app().app_context():
        yield


@dataclass
class FileCompat:
    """Compatibility wrapper to emulate Werkzeug FileStorage interface."""

    source: UploadFile

    @property
    def filename(self) -> str | None:
        return self.source.filename

    def save(self, dst: str) -> None:
        path = Path(dst)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.source.file.seek(0)
        path.write_bytes(self.source.file.read())


def as_jsonable(value: Any) -> Any:
    """Normalize Flask tuple responses to plain JSON body + status code tuple."""
    if isinstance(value, tuple) and len(value) == 2:
        return value
    return value, 200


class LegacyServiceAdapter:
    """Facade for legacy handlers callable from FastAPI routers."""

    @staticmethod
    def get_questions_api(*, page: int, page_count: int, public_only: bool):
        with flask_context():
            records, total_count = get_questions_api_data(page=page, page_count=page_count, public_only=public_only)
        return records, total_count

    @staticmethod
    def form_questions_list(payload: dict[str, Any]):
        with flask_context():
            if payload.get("findquestioninlist"):
                return as_jsonable(find_question_in_list(payload))
            return as_jsonable(form_questions_list(payload))

    @staticmethod
    def get_roles(payload: dict[str, Any]):
        with flask_context():
            return as_jsonable(get_roles_by_space(payload.get("spaceid"), payload.get("roleid"), payload.get("userid")))

    @staticmethod
    def save_or_update(action: str, payload: dict[str, Any]):
        with flask_context():
            if action == "save_question":
                return as_jsonable(save_question(payload))
            if action == "save_combine":
                return as_jsonable(save_combine(payload))
            if action == "save_anonym_question":
                return as_jsonable(save_anonym_question(payload))
        return {"status": "error", "error_mess": "WARN: No valid action param"}, 200

    @staticmethod
    def service_action(payload: dict[str, Any]):
        with flask_context():
            action = payload.get("action")
            if action == "execaction":
                return as_jsonable(exec_action(payload.get("execute_action"), payload.get("orderid"), payload.get("userid")))
            if action == "changefilepublicity":
                return as_jsonable(change_attach_publicity(payload.get("attachid"), payload.get("publicflag")))
            if action == "deleteattachment":
                return as_jsonable(delete_attachment(payload.get("attach_target"), payload.get("attachid"), payload.get("orderid"), payload.get("userid")))
            if action == "createnewadmin":
                return as_jsonable(create_new_admin(payload.get("edulogin"), payload.get("adminlogin"), payload.get("adminpass")))
            if action == "changeadminpass":
                return as_jsonable(change_admin_pass(payload.get("userid"), payload.get("adminpass")))
            if action == "updateappconfig":
                return as_jsonable(update_app_config(payload))
            if action == "getappconfiginfo":
                return as_jsonable(get_appconfig_info())
            if action == "enteradmin":
                return as_jsonable(enter_admin(payload.get("adminlogin"), payload.get("adminpass"), payload.get("userid")))
            if action == "exitadmin":
                return as_jsonable(exit_admin(payload.get("userid")))
            if action == "updtspacesbyconfl":
                from tasks.updatespaceinfo import update_spaces_info

                update_spaces_info.delay()
                return {"status": "ok"}, 200

        return {"status": "error", "error_mess": "WARN: No valid action param"}, 200

    @staticmethod
    def statistic(payload: dict[str, Any]):
        with flask_context():
            delta = "7day" if int(payload.get("botimeperiod", 0)) == 7 else "30day"
            if payload.get("botstatskind") == "newusers":
                return as_jsonable(get_newuser_stat(delta, payload.get("botdownloadflag")))
            if payload.get("botstatskind") == "phrazestats":
                return as_jsonable(get_phraze_stat(delta, payload.get("botdownloadflag")))
            if payload.get("botstatskind") == "phrazesperday":
                return as_jsonable(get_perdayphrazes_stat(delta, payload.get("botdownloadflag")))
        return {"status": "error", "error_mess": "WARN: No params"}, 200

    @staticmethod
    def botexcel(payload: dict[str, Any]):
        with flask_context():
            action = payload.get("action")
            chatid = payload.get("chatid")

            _tg_post(
                get_legacy_flask_app().config["TEL_SENDMESS_URL"],
                json_body={
                    "chat_id": chatid,
                    "text": "⚠ <b>Запрос принят. Ожидайте ваш файл с результатами</b>",
                    "parse_mode": "html",
                },
                timeout=(10.0, 40.0),
                socks_proxy=get_legacy_flask_app().config["TEL_SOCKS_PROXY"],
            )

            if action == "getfollowersexcel":
                from tasks.getfollowers import get_followers_excel

                if get_legacy_flask_app().config["FLASK_ENV"] == "production":
                    get_followers_excel.delay(chatid)
                else:
                    get_followers_excel(chatid)
                return {"status": "ok"}, 200

            if action == "getsuppinfo":
                from tasks.getsuppinfo import get_supp_info

                if get_legacy_flask_app().config["FLASK_ENV"] == "production":
                    get_supp_info.delay(chatid)
                else:
                    get_supp_info(chatid)
                return {"status": "ok"}, 200

        return {"status": "error", "error_mess": "WARN: No valid action param"}, 200
