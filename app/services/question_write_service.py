"""Native command service for question write flows.

The module keeps legacy response envelopes intact while routing FastAPI write
operations directly to migrated handlers (without the legacy bridge).
"""

from __future__ import annotations

from typing import Any

from app.services.questions_write import save_anonym_question
from app.services.questions_write import save_combine
from app.services.questions_write import save_question


class QuestionWriteService:
    """Dispatch `/saveorupdate/` actions to native write handlers."""

    @staticmethod
    def execute(action: str, payload: dict[str, Any]) -> tuple[dict[str, Any], int]:
        if action == "save_question":
            return save_question(payload), 200
        if action == "save_combine":
            return save_combine(payload), 200
        if action == "save_anonym_question":
            return save_anonym_question(payload), 200
        return {"status": "error", "error_mess": "WARN: No valid action param"}, 200

