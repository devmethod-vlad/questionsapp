"""Admin/support application services used by FastAPI routers."""

from __future__ import annotations

from typing import Any

from fastapi.responses import Response

from app.repositories.admin_repository import SqlAlchemyAdminRepository
from app.services.admin_actions_service import AdminActionsService
from app.services.admin_legacy_compat_service import AdminLegacyCompatService
from app.services.question_action_service import QuestionActionService


def _admin_actions_service(session) -> AdminActionsService:
    """Build native admin actions service for the current request session."""

    return AdminActionsService(repository=SqlAlchemyAdminRepository(session=session))


class AdminService:
    """Application service for non-question support/admin actions."""

    @staticmethod
    def get_space_roles(payload: dict[str, Any], *, session):
        return _admin_actions_service(session).get_roles_by_space(
            spaceid=payload.get("spaceid"),
            roleid=payload.get("roleid"),
            userid=payload.get("userid"),
        ), 200

    @staticmethod
    def execute_service_action(payload: dict[str, Any], *, session):
        question_action_response = QuestionActionService.execute(payload, session=session)
        if question_action_response is not None:
            return question_action_response, 200

        native_response = _admin_actions_service(session).execute_service_action(payload)
        if native_response is not None:
            return native_response, 200

        compat_response = AdminLegacyCompatService.execute_service_action(payload, session=session)
        if compat_response is not None:
            return compat_response, 200

        return {"status": "error", "error_mess": "WARN: No valid action param"}, 200

    @staticmethod
    def get_statistics(payload: dict[str, Any], *, session) -> tuple[dict[str, Any], int] | Response:
        response = AdminLegacyCompatService.get_statistics(payload, session=session)
        if isinstance(response, Response):
            return response
        return response, 200

    @staticmethod
    def build_bot_excel(payload: dict[str, Any]):
        return AdminLegacyCompatService.build_bot_excel(payload), 200
