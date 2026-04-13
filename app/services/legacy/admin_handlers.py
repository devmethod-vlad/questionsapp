"""Adapters for admin/support utility endpoints."""

from __future__ import annotations

from typing import Any

from app.services.legacy_bridge import LegacyServiceAdapter


class LegacyAdminHandlers:
    """Facade used by FastAPI routers for non-question domain actions."""

    @staticmethod
    def space_roles(payload: dict[str, Any]):
        return LegacyServiceAdapter.get_roles(payload)

    @staticmethod
    def service(payload: dict[str, Any]):
        return LegacyServiceAdapter.service_action(payload)

    @staticmethod
    def statistic(payload: dict[str, Any]):
        return LegacyServiceAdapter.statistic(payload)

    @staticmethod
    def botexcel(payload: dict[str, Any]):
        return LegacyServiceAdapter.botexcel(payload)
