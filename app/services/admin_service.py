"""Admin/support application services used by FastAPI routers."""

from __future__ import annotations

from typing import Any

from app.repositories.admin_repository import SqlAlchemyAdminRepository
from app.services.admin_actions_service import AdminActionsService
from app.services.legacy_bridge import LegacyServiceAdapter
from app.services.question_action_service import QuestionActionService


def _admin_actions_service() -> AdminActionsService:
    """Build native admin actions service.

    Kept as a lightweight factory because current FastAPI endpoints still use
    static service methods for backward-compatibility.
    """

    return AdminActionsService(repository=SqlAlchemyAdminRepository())


class AdminService:
    """Application service for non-question support/admin actions."""

    @staticmethod
    def get_space_roles(payload: dict[str, Any]):
        return _admin_actions_service().get_roles_by_space(
            spaceid=payload.get("spaceid"),
            roleid=payload.get("roleid"),
            userid=payload.get("userid"),
        ), 200

    @staticmethod
    def execute_service_action(payload: dict[str, Any]):
        question_action_response = QuestionActionService.execute(payload)
        if question_action_response is not None:
            return question_action_response, 200

        native_response = _admin_actions_service().execute_service_action(payload)
        if native_response is not None:
            return native_response, 200
        legacy_adapter = LegacyServiceAdapter
        return legacy_adapter.service_action(payload)

    @staticmethod
    def get_statistics(payload: dict[str, Any]):
        return LegacyServiceAdapter.statistic(payload)

    @staticmethod
    def build_bot_excel(payload: dict[str, Any]):
        return LegacyServiceAdapter.botexcel(payload)
