"""Repositories for admin/roles/app-config flows.

The goal of this module is to keep ORM data access in one place so service
layers can focus on orchestration and legacy-compatible response shaping.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.db.models import (
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

    session: object

    def get_manual_user_by_login(self, *, login: str) -> UserManualInfo | None:
        return self.session.query(UserManualInfo).filter_by(login=login).first()

    def get_manual_user_by_user_id(self, *, user_id: int) -> UserManualInfo | None:
        return self.session.query(UserManualInfo).filter_by(userid=user_id).first()

    def get_wiki_user_by_login(self, *, login: str) -> UserWikiInfo | None:
        return self.session.query(UserWikiInfo).filter_by(login=login).first()

    def get_user_base_role(self, *, user_id: int) -> UserBaseRole | None:
        return self.session.query(UserBaseRole).filter_by(userid=user_id).first()

    def get_union_role(self, *, role_id: int) -> UnionRole | None:
        return self.session.query(UnionRole).filter_by(id=role_id).first()

    def list_space_union_roles(self, *, space_id: int) -> list[SpaceUnionRole]:
        return self.session.query(SpaceUnionRole).filter(SpaceUnionRole.spaceid == space_id).all()

    def list_user_union_roles(self, *, user_id: int) -> list[UserUnionRole]:
        return self.session.query(UserUnionRole).filter(UserUnionRole.userid == user_id).all()

    def remove_access_token(self, *, user_id: int) -> None:
        token = self.session.query(AccessToken).filter_by(userid=user_id).first()
        if token is not None:
            self.session.delete(token)

    def add_access_token(self, *, user_id: int, token: str) -> None:
        self.session.add(AccessToken(userid=user_id, token=token))

    def add_manual_user(self, *, user_id: int, login: str, password_hash: str) -> None:
        self.session.add(UserManualInfo(userid=user_id, login=login, password=password_hash))

    def get_app_config(self) -> AppConfig | None:
        return self.session.query(AppConfig).first()

    def update_app_config(self, *, config_id: int, token_expire: int, botname: str, uploadsize: int) -> None:
        self.session.query(AppConfig).filter_by(id=config_id).update(
            {
                "token_expire": token_expire,
                "botname": botname,
                "uploadsize": uploadsize,
            }
        )

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()

    def add(self, entity: object) -> None:
        self.session.add(entity)
