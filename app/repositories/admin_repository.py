"""Repositories for admin/roles/app-config flows.

The goal of this module is to keep ORM data access in one place so service
layers can focus on orchestration and legacy-compatible response shaping.
"""

from __future__ import annotations

from dataclasses import dataclass

from questionsapp.models import (
    AccessToken,
    AppConfig,
    SpaceUnionRole,
    UnionRole,
    UserBaseRole,
    UserManualInfo,
    UserUnionRole,
    UserWikiInfo,
)


@dataclass(slots=True)
class SqlAlchemyAdminRepository:
    """SQLAlchemy-backed helpers for admin and role workflows."""

    def get_manual_user_by_login(self, *, login: str) -> UserManualInfo | None:
        return UserManualInfo.query.filter_by(login=login).first()

    def get_manual_user_by_user_id(self, *, user_id: int) -> UserManualInfo | None:
        return UserManualInfo.query.filter_by(userid=user_id).first()

    def get_wiki_user_by_login(self, *, login: str) -> UserWikiInfo | None:
        return UserWikiInfo.query.filter_by(login=login).first()

    def get_user_base_role(self, *, user_id: int) -> UserBaseRole | None:
        return UserBaseRole.query.filter_by(userid=user_id).first()

    def get_union_role(self, *, role_id: int) -> UnionRole | None:
        return UnionRole.query.filter_by(id=role_id).first()

    def list_space_union_roles(self, *, space_id: int) -> list[SpaceUnionRole]:
        return SpaceUnionRole.query.filter(SpaceUnionRole.spaceid == space_id).all()

    def list_user_union_roles(self, *, user_id: int) -> list[UserUnionRole]:
        return UserUnionRole.query.filter(UserUnionRole.userid == user_id).all()

    def remove_access_token(self, *, user_id: int) -> None:
        token = AccessToken.query.filter_by(userid=user_id).first()
        if token is not None:
            from database import db

            db.session.delete(token)

    def add_access_token(self, *, user_id: int, token: str) -> None:
        from database import db

        db.session.add(AccessToken(userid=user_id, token=token))

    def add_manual_user(self, *, user_id: int, login: str, password_hash: str) -> None:
        from database import db

        db.session.add(UserManualInfo(userid=user_id, login=login, password=password_hash))

    def get_app_config(self) -> AppConfig | None:
        return AppConfig.query.first()

    def update_app_config(self, *, config_id: int, token_expire: int, botname: str, uploadsize: int) -> None:
        AppConfig.query.filter_by(id=config_id).update(
            {
                "token_expire": token_expire,
                "botname": botname,
                "uploadsize": uploadsize,
            }
        )
