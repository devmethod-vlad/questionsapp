"""Token validation for legacy `/questionslist/` sync mode."""

from __future__ import annotations

import datetime

import pytz

from app.db.legacy_db import db
from app.services.auth.user_info_service import set_user_info
from app.db.models import AccessToken, AppConfig

LOCAL_TIMEZONE = pytz.timezone("Europe/Moscow")


def check_user_token(token: str | None) -> dict:
    """Validate token and return legacy-compatible status payload."""

    if not token:
        return {"status": "error", "error_mess": "WARN: No token param"}

    try:
        config_rec = db.session.query(AppConfig).first()
        if config_rec is None:
            return {"status": "error", "error_mess": "WARN: No appconfig record"}

        token_rec = db.session.query(AccessToken).filter_by(token=token).first()
        if token_rec is None:
            return {"status": "token_error", "error_mess": "WARN: Token doesn't find"}

        created_date = token_rec.created_at.astimezone(LOCAL_TIMEZONE)
        now = datetime.datetime.now(pytz.utc).astimezone(LOCAL_TIMEZONE)
        diff_min = abs((now - created_date).total_seconds() / 60)

        if diff_min > config_rec.token_expire:
            db.session.delete(token_rec)
            db.session.commit()
            return {"status": "token_expire"}

        payload = {"token": token_rec.token}
        payload.update(set_user_info(token_rec.userid))
        return {"status": "ok", "info": payload}
    except Exception:
        return {"status": "error", "error_mess": "WARN: Error during checking token"}
