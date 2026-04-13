"""Admin/support application services used by FastAPI routers."""

from __future__ import annotations

from typing import Any

from app.services.legacy.questions.execaction import exec_action
from app.workers.tasks.getfollowers import get_followers_excel
from app.workers.tasks.getsuppinfo import get_supp_info
from app.workers.tasks.updatespaceinfo import update_spaces_info
from questionsapp.services.appconfig.getappconfig import get_appconfig_info
from questionsapp.services.appconfig.updateconfig import update_app_config
from questionsapp.services.attachments.changeatttachpublicity import change_attach_publicity
from questionsapp.services.attachments.deleteattachment import delete_attachment
from questionsapp.services.auxillary.getrolesbyspace import get_roles_by_space
from questionsapp.services.auxillary.telegram import _tg_post
from questionsapp.services.roles.changeadminpass import change_admin_pass
from questionsapp.services.roles.createnewadmin import create_new_admin
from questionsapp.services.roles.enteradmin import enter_admin
from questionsapp.services.roles.exitadmin import exit_admin
from questionsapp.services.stats.bot.getnewuser import get_newuser_stat
from questionsapp.services.stats.bot.getphrazestat import get_phraze_stat
from questionsapp.services.stats.bot.phrazesperdaystat import get_perdayphrazes_stat
from app.core.legacy_runtime import app as legacy_app


def as_jsonable(value: Any) -> tuple[Any, int]:
    if isinstance(value, tuple) and len(value) == 2:
        return value
    return value, 200


class AdminService:
    """Application service for non-question support/admin actions."""

    @staticmethod
    def get_space_roles(payload: dict[str, Any]):
        return as_jsonable(get_roles_by_space(payload.get("spaceid"), payload.get("roleid"), payload.get("userid")))

    @staticmethod
    def execute_service_action(payload: dict[str, Any]):
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
            update_spaces_info.delay()
            return {"status": "ok"}
        return {"status": "error", "error_mess": "WARN: No valid action param"}, 200

    @staticmethod
    def get_statistics(payload: dict[str, Any]):
        delta = "7day" if int(payload.get("botimeperiod", 0)) == 7 else "30day"
        if payload.get("botstatskind") == "newusers":
            return as_jsonable(get_newuser_stat(delta, payload.get("botdownloadflag")))
        if payload.get("botstatskind") == "phrazestats":
            return as_jsonable(get_phraze_stat(delta, payload.get("botdownloadflag")))
        if payload.get("botstatskind") == "phrazesperday":
            return as_jsonable(get_perdayphrazes_stat(delta, payload.get("botdownloadflag")))
        return {"status": "error", "error_mess": "WARN: No params"}, 200

    @staticmethod
    def build_bot_excel(payload: dict[str, Any]):
        action = payload.get("action")
        chatid = payload.get("chatid")
        _tg_post(
            legacy_app.config["TEL_SENDMESS_URL"],
            json_body={
                "chat_id": chatid,
                "text": "⚠ <b>Запрос принят. Ожидайте ваш файл с результатами</b>",
                "parse_mode": "html",
            },
            timeout=(10.0, 40.0),
            socks_proxy=legacy_app.config["TEL_SOCKS_PROXY"],
        )
        if action == "getfollowersexcel":
            if legacy_app.config["FLASK_ENV"] == "production":
                get_followers_excel.delay(chatid)
            else:
                get_followers_excel(chatid)
            return {"status": "ok"}, 200
        if action == "getsuppinfo":
            if legacy_app.config["FLASK_ENV"] == "production":
                get_supp_info.delay(chatid)
            else:
                get_supp_info(chatid)
            return {"status": "ok"}, 200
        return {"status": "error", "error_mess": "WARN: No valid action param"}, 200
