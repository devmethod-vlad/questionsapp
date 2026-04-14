"""Token validation for legacy `/questionslist/` sync mode."""

from __future__ import annotations

import datetime

import pytz

from app.repositories.auth_repository import SqlAlchemyAuthRepository
from app.services.auth.user_info_service import set_user_info

LOCAL_TIMEZONE = pytz.timezone("Europe/Moscow")


def check_user_token(token: str | None, repository: SqlAlchemyAuthRepository) -> dict:
    """Validate token and return legacy-compatible status payload."""

    if not token:
        return {"status": "error", "error_mess": "WARN: No token param"}

    try:
        config_rec = repository.get_app_config()
        if config_rec is None:
            return {"status": "error", "error_mess": "WARN: No appconfig record"}

        token_rec = repository.get_access_token(token=token)
        if token_rec is None:
            return {"status": "token_error", "error_mess": "WARN: Token doesn't find"}

        created_date = token_rec.created_at.astimezone(LOCAL_TIMEZONE)
        now = datetime.datetime.now(pytz.utc).astimezone(LOCAL_TIMEZONE)
        diff_min = abs((now - created_date).total_seconds() / 60)

        if diff_min > config_rec.token_expire:
            repository.remove_access_token(token_record=token_rec)
            repository.commit()
            return {"status": "token_expire"}

        payload = {"token": token_rec.token}
        payload.update(set_user_info(token_rec.userid, repository=repository))
        return {"status": "ok", "info": payload}
    except Exception:
        return {"status": "error", "error_mess": "WARN: Error during checking token"}
