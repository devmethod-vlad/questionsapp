"""Admin/support application services used by FastAPI routers."""

from __future__ import annotations

from typing import Any

from app.services.legacy_bridge import LegacyServiceAdapter


class AdminService:
    """Application service for non-question support/admin actions."""

    @staticmethod
    def get_space_roles(payload: dict[str, Any]):
        return LegacyServiceAdapter.get_roles(payload)

    @staticmethod
    def execute_service_action(payload: dict[str, Any]):
        return LegacyServiceAdapter.service_action(payload)

    @staticmethod
    def get_statistics(payload: dict[str, Any]):
        return LegacyServiceAdapter.statistic(payload)

    @staticmethod
    def build_bot_excel(payload: dict[str, Any]):
        return LegacyServiceAdapter.botexcel(payload)
