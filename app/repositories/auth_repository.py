"""Repository helpers for auth/user-info workflows."""

from __future__ import annotations

from dataclasses import dataclass

from app.db.models import (
    AccessToken,
    AppConfig,
    BaseRole,
    User,
    UserBaseRole,
    UserEmiasInfo,
    UserManualInfo,
    UserTelegramInfo,
    UserWikiInfo,
)


@dataclass(slots=True)
class SqlAlchemyAuthRepository:
    """SQLAlchemy-backed read/write helpers used by auth services."""

    session: object

    def get_app_config(self) -> AppConfig | None:
        return self.session.query(AppConfig).first()

    def get_access_token(self, *, token: str) -> AccessToken | None:
        return self.session.query(AccessToken).filter_by(token=token).first()

    def remove_access_token(self, *, token_record: AccessToken) -> None:
        self.session.delete(token_record)

    def get_user(self, *, user_id: int) -> User | None:
        return self.session.query(User).filter_by(id=user_id).first()

    def get_user_telegram_info(self, *, user_id: int) -> UserTelegramInfo | None:
        return self.session.query(UserTelegramInfo).filter_by(userid=user_id).first()

    def get_user_base_role(self, *, user_id: int) -> UserBaseRole | None:
        return self.session.query(UserBaseRole).filter_by(userid=user_id).first()

    def get_base_role(self, *, role_id: int) -> BaseRole | None:
        return self.session.query(BaseRole).filter_by(id=role_id).first()

    def get_user_manual_info(self, *, user_id: int) -> UserManualInfo | None:
        return self.session.query(UserManualInfo).filter_by(userid=user_id).first()

    def get_user_emias_info(self, *, user_id: int) -> UserEmiasInfo | None:
        return self.session.query(UserEmiasInfo).filter_by(userid=user_id).first()

    def get_user_wiki_info(self, *, user_id: int) -> UserWikiInfo | None:
        return self.session.query(UserWikiInfo).filter_by(userid=user_id).first()

    def commit(self) -> None:
        self.session.commit()
