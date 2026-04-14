"""User profile payload builders used by legacy-compatible endpoints."""

from __future__ import annotations

from app.db.legacy_db import db
from app.db.models import BaseRole, User, UserBaseRole, UserEmiasInfo, UserManualInfo, UserTelegramInfo, UserWikiInfo


def set_user_info(userid: int, onlyreginfo: bool = False) -> dict:
    """Build legacy-compatible user info payload.

    Important: output keys must stay unchanged for backward compatibility.
    """

    telegram_rec = db.session.query(UserTelegramInfo).filter_by(userid=userid).first()
    tel_reg = 1 if telegram_rec is not None else 0

    if onlyreginfo:
        return {"appreginfо": {"telegram": tel_reg}}

    user_role_rec = db.session.query(UserBaseRole).filter_by(userid=userid).first()
    if user_role_rec is not None:
        role_rec = db.session.query(BaseRole).filter_by(id=user_role_rec.roleid).first()
        userrole = {"id": user_role_rec.roleid, "name": role_rec.name if role_rec else ""}
    else:
        userrole = {"id": 0, "name": ""}

    user_admin_rec = db.session.query(UserManualInfo).filter_by(userid=userid).first()
    adminlogin = user_admin_rec.login if user_admin_rec is not None else ""

    user_emias_rec = db.session.query(UserEmiasInfo).filter_by(userid=userid).first()
    emiaslogin = user_emias_rec.emiaslogin if user_emias_rec is not None else ""

    user_wiki_rec = db.session.query(UserWikiInfo).filter_by(userid=userid).first()
    wikilogin = user_wiki_rec.login if user_wiki_rec is not None else ""

    user_rec = db.session.query(User).filter_by(id=userid).first()
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
