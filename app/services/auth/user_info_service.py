"""User profile payload builders used by legacy-compatible endpoints."""

from __future__ import annotations

from questionsapp.models import BaseRole, User, UserBaseRole, UserEmiasInfo, UserManualInfo, UserTelegramInfo, UserWikiInfo


def set_user_info(userid: int, onlyreginfo: bool = False) -> dict:
    """Build legacy-compatible user info payload.

    Important: output keys must stay unchanged for backward compatibility.
    """

    telegram_rec = UserTelegramInfo.query.filter_by(userid=userid).first()
    tel_reg = 1 if telegram_rec is not None else 0

    if onlyreginfo:
        return {"appreginfо": {"telegram": tel_reg}}

    user_role_rec = UserBaseRole.query.filter_by(userid=userid).first()
    if user_role_rec is not None:
        role_rec = BaseRole.query.filter_by(id=user_role_rec.roleid).first()
        userrole = {"id": user_role_rec.roleid, "name": role_rec.name if role_rec else ""}
    else:
        userrole = {"id": 0, "name": ""}

    user_admin_rec = UserManualInfo.query.filter_by(userid=userid).first()
    adminlogin = user_admin_rec.login if user_admin_rec is not None else ""

    user_emias_rec = UserEmiasInfo.query.filter_by(userid=userid).first()
    emiaslogin = user_emias_rec.emiaslogin if user_emias_rec is not None else ""

    user_wiki_rec = UserWikiInfo.query.filter_by(userid=userid).first()
    wikilogin = user_wiki_rec.login if user_wiki_rec is not None else ""

    user_rec = User.query.filter_by(id=userid).first()
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
