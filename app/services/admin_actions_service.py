"""Native admin/support action handlers.

These helpers preserve legacy response envelopes while removing runtime
coupling to Flask application context and the legacy bridge.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from typing import Any

import bcrypt

from app.core.runtime_config import get_base_roles, get_default_format, get_null_space
from app.repositories.admin_repository import SqlAlchemyAdminRepository
from app.services.legacy.roles.getrole import get_role
from app.services.auth.user_info_service import set_user_info


@dataclass(slots=True)
class AdminActionsService:
    """Application service for role/admin/app-config related operations."""

    repository: SqlAlchemyAdminRepository

    def get_roles_by_space(self, *, spaceid: int | None, roleid: int | None, userid: int | None) -> dict[str, Any]:
        if not spaceid or not roleid:
            return {"status": "error", "error_mess": "WARN: No spaceid param"}

        role = get_role(roleid)
        if not role:
            return {"status": "error", "error_mess": "WARN: No role"}

        role_list: list[dict[str, Any]] = []
        if role in {"redactor", "admin"}:
            for space_role in self.repository.list_space_union_roles(space_id=int(spaceid)):
                role_rec = self.repository.get_union_role(role_id=space_role.unionroleid)
                if role_rec:
                    role_list.append({"id": role_rec.id, "emiasid": role_rec.emiasid, "name": role_rec.name})
        else:
            user_roles = self.repository.list_user_union_roles(user_id=int(userid)) if userid is not None else []
            user_role_ids = [item.unionroleid for item in user_roles]
            if int(spaceid) != int(get_null_space()["id"]):
                for space_role in self.repository.list_space_union_roles(space_id=int(spaceid)):
                    role_rec = self.repository.get_union_role(role_id=space_role.unionroleid)
                    if role_rec and role_rec.emiasid != 0 and role_rec.id in user_role_ids:
                        role_list.append({"id": role_rec.id, "emiasid": role_rec.emiasid, "name": role_rec.name})
            else:
                for role_id in user_role_ids:
                    role_rec = self.repository.get_union_role(role_id=role_id)
                    if role_rec and role_rec.emiasid != 0:
                        role_list.append({"id": role_rec.id, "emiasid": role_rec.emiasid, "name": role_rec.name})

        if len(role_list) > 1:
            role_list = sorted(role_list, key=lambda item: item["name"])

        return {"status": "ok", "info": {"roles_list": role_list}}

    def execute_service_action(self, payload: dict[str, Any]):
        action = payload.get("action")
        if action == "createnewadmin":
            return self.create_new_admin(
                edulogin=payload.get("edulogin"),
                adminlogin=payload.get("adminlogin"),
                adminpass=payload.get("adminpass"),
            )
        if action == "changeadminpass":
            return self.change_admin_pass(userid=payload.get("userid"), adminpass=payload.get("adminpass"))
        if action == "updateappconfig":
            return self.update_app_config(payload)
        if action == "getappconfiginfo":
            return self.get_app_config_info()
        if action == "enteradmin":
            return self.enter_admin(
                login=payload.get("adminlogin"),
                password=payload.get("adminpass"),
                userid=payload.get("userid"),
            )
        if action == "exitadmin":
            return self.exit_admin(userid=payload.get("userid"))

        return None

    def create_new_admin(self, *, edulogin: str | None, adminlogin: str | None, adminpass: str | None):
        if not edulogin or not adminlogin or not adminpass:
            return {"status": "params_error", "error_mess": "WARN: No params"}

        check_wiki_info = self.repository.get_wiki_user_by_login(login=edulogin)
        if check_wiki_info is None:
            return {
                "status": "error",
                "error_mess": "WARN: No wiki info",
                "info": "Пользователь с таким логином никогда не пользовался функционалом Вопросов/Ответов",
            }

        if self.repository.get_manual_user_by_user_id(user_id=check_wiki_info.userid) is not None:
            return {
                "status": "error",
                "error_mess": "WARN: admin already exist",
                "info": "Пользователь с таким логином уже зарегистрирован в качестве администратора",
            }

        user_role = self.repository.get_user_base_role(user_id=check_wiki_info.userid)
        if user_role is None or user_role.roleid != 3:
            return {
                "status": "error",
                "error_mess": "WARN: incorrect user role",
                "info": "Пользователь c данной ролью не может быть зарегистрирован в качесте администратора",
            }

        if self.repository.get_manual_user_by_login(login=adminlogin) is not None:
            return {
                "status": "error",
                "error_mess": "WARN: login already exist",
                "info": "Пользователь с таким логином уже зарегистрирован в качестве администратора",
            }

        if len(adminlogin) <= 4:
            return {
                "status": "error",
                "error_mess": "WARN: login less then 4 symbols",
                "info": "Логин администратора должен состоять как минимум из 4 символов",
            }

        try:
            hashed = bcrypt.hashpw(adminpass.encode(get_default_format()), bcrypt.gensalt())
            self.repository.add_manual_user(
                user_id=check_wiki_info.userid,
                login=adminlogin,
                password_hash=hashed.decode(get_default_format()),
            )
            self.repository.commit()
            return {"status": "ok"}
        except Exception as exc:  # pragma: no cover - legacy-compatible envelope
            self.repository.rollback()
            return {"status": "error", "error_mess": str(exc)}

    def change_admin_pass(self, *, userid: int | None, adminpass: str | None):
        if not adminpass or not userid:
            return {"status": "params_error", "error_mess": "WARN: No params"}

        manual_user = self.repository.get_manual_user_by_user_id(user_id=int(userid))
        if manual_user is None:
            return {"status": "error", "error_mess": "Admin doesn't exist"}

        try:
            hashed = bcrypt.hashpw(adminpass.encode(get_default_format()), bcrypt.gensalt())
            manual_user.password = hashed.decode(get_default_format())
            self.repository.commit()
            return {"status": "ok"}
        except Exception as exc:  # pragma: no cover - legacy-compatible envelope
            self.repository.rollback()
            return {"status": "error", "error_mess": str(exc)}

    def enter_admin(self, *, login: str | None, password: str | None, userid: int | None):
        if not login or not password or not userid:
            return {"status": "error", "error_mess": "WARN: No params"}

        check_admin = self.repository.get_manual_user_by_login(login=login)
        if check_admin is None or check_admin.userid != int(userid):
            return {"status": "not_found", "error_mess": "WARN: Login not found"}

        if not bcrypt.checkpw(password.encode(get_default_format()), check_admin.password.encode("UTF-8")):
            return {"status": "not_match", "error_mess": "WARN: Data is incorrect"}

        check_role = self.repository.get_user_base_role(user_id=check_admin.userid)
        if check_role is None:
            return {"status": "error", "error_mess": "WARN: No user role rec"}

        check_role.roleid = 1
        self.repository.add(check_role)

        access_token = secrets.token_urlsafe(16)
        self.repository.remove_access_token(user_id=check_admin.userid)
        self.repository.commit()

        self.repository.add_access_token(user_id=check_admin.userid, token=access_token)
        user_info = set_user_info(check_admin.userid)
        userinfo = {"token": access_token}
        userinfo.update(user_info)
        userinfo["userrole"] = {"id": 1, "name": "Администратор"}
        self.repository.commit()
        return {"status": "ok", "info": userinfo}

    def exit_admin(self, *, userid: int | None):
        if not userid:
            return {"status": "error", "error_mess": "WARN: No userid"}

        check_role = self.repository.get_user_base_role(user_id=int(userid))
        if check_role is None:
            return {"status": "error", "error_mess": "WARN: No user role rec"}

        base_roles = get_base_roles()
        if check_role.roleid == int(base_roles["admin"]["id"]):
            check_role.roleid = int(base_roles["redactor"]["id"])
            self.repository.commit()

        return {"status": "ok"}

    def get_app_config_info(self):
        check_config = self.repository.get_app_config()
        if check_config is None:
            return {"status": "error", "error_mess": "WARN: No config"}

        return {
            "status": "ok",
            "info": {
                "token_expire": check_config.token_expire,
                "botname": check_config.botname,
                "uploadsize": check_config.uploadsize,
                "maxfiles": check_config.maxfiles,
                "anonymuserid": check_config.anonymuserid,
                "ispublicactive": check_config.ispublicactive,
            },
        }

    def update_app_config(self, payload: dict[str, Any]):
        if not payload.get("tokenlifetime") or not payload.get("botname") or not payload.get("uploadsize"):
            return {"status": "params_error", "error_mess": "WARN: No params"}

        try:
            config_rec = self.repository.get_app_config()
            if config_rec is None:
                return {"status": "error", "error_mess": "WARN: No config"}

            self.repository.update_app_config(
                config_id=config_rec.id,
                token_expire=int(payload["tokenlifetime"]),
                botname=payload["botname"],
                uploadsize=int(payload["uploadsize"]),
            )
            self.repository.commit()
            return {"status": "ok"}
        except Exception as exc:  # pragma: no cover - legacy-compatible envelope
            self.repository.rollback()
            return {"status": "error", "error_mess": str(exc)}
