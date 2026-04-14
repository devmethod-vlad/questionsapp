"""Native command service for question-level admin actions."""

from __future__ import annotations

from typing import Any

from app.services.questions_write import exec_action


class QuestionActionService:
    """Handle service actions that mutate question state."""

    @staticmethod
    def execute(payload: dict[str, Any], *, session) -> dict[str, Any] | None:
        if payload.get("action") != "execaction":
            return None
        return exec_action(payload.get("execute_action"), payload.get("orderid"), payload.get("userid"), session=session)
