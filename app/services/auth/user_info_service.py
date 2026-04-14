"""User profile payload builders used by legacy-compatible endpoints."""

from __future__ import annotations

from app.repositories.auth_repository import SqlAlchemyAuthRepository


def set_user_info(userid: int, repository: SqlAlchemyAuthRepository, onlyreginfo: bool = False) -> dict:
    """Build legacy-compatible user info payload.

    Important: output keys must stay unchanged for backward compatibility.
    """

    telegram_rec = repository.get_user_telegram_info(user_id=userid)
    tel_reg = 1 if telegram_rec is not None else 0

    if onlyreginfo:
        return {"appreginfо": {"telegram": tel_reg}}

    user_role_rec = repository.get_user_base_role(user_id=userid)
    if user_role_rec is not None:
        role_rec = repository.get_base_role(role_id=user_role_rec.roleid)
        userrole = {"id": user_role_rec.roleid, "name": role_rec.name if role_rec else ""}
    else:
        userrole = {"id": 0, "name": ""}

    user_admin_rec = repository.get_user_manual_info(user_id=userid)
    adminlogin = user_admin_rec.login if user_admin_rec is not None else ""

    user_emias_rec = repository.get_user_emias_info(user_id=userid)
    emiaslogin = user_emias_rec.emiaslogin if user_emias_rec is not None else ""

    user_wiki_rec = repository.get_user_wiki_info(user_id=userid)
    wikilogin = user_wiki_rec.login if user_wiki_rec is not None else ""

    user_rec = repository.get_user(user_id=userid)
    return {
        "userid": userid,
        "appreginfo": {"telegram": tel_reg},
        "wikilogin": wikilogin,
        "userlastname": user_rec.lastname,
        "userfirstname": user_rec.firstname,
        "emiaslogin": emiaslogin,
        "usersecondname": user_rec.secondname,
        "userrole": userrole,
        "adminlogin": adminlogin,
    }
