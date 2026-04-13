"""Question-domain application services preserving legacy API contracts."""

from __future__ import annotations

from typing import Any

from dataclasses import dataclass
from pathlib import Path

from fastapi import UploadFile

from app.repositories.questions_repository import QuestionsReadRepository
from app.services.legacy.questions.get_questions_api import get_questions_api_data
from app.services.legacy.questions.saveanonymquestion import save_anonym_question
from app.services.legacy.questions.savecombine import save_combine
from app.services.legacy.questions.savequestion import save_question
from questionsapp.services.questionslist.formquestionslist import find_question_in_list, form_questions_list


def as_jsonable(value: Any) -> tuple[Any, int]:
    if isinstance(value, tuple) and len(value) == 2:
        return value
    return value, 200


class QuestionsService:
    """Application service for question-related operations."""

    def __init__(self, *, questions_read_repository: QuestionsReadRepository):
        self._questions_read_repository = questions_read_repository

    def get_public_questions(self, *, page: int, page_count: int, public_only: bool):
        """Return public questions through repository abstraction."""
        return get_questions_api_data(
            page=page,
            page_count=page_count,
            public_only=public_only,
            repository=self._questions_read_repository,
        )

    @staticmethod
    def get_questions_list(payload: dict[str, Any]):
        if payload.get("findquestioninlist"):
            return as_jsonable(find_question_in_list(payload))
        return as_jsonable(form_questions_list(payload))

    @staticmethod
    def save_or_update(action: str, payload: dict[str, Any], question_files: list[Any], answer_files: list[Any]):
        wrapped_payload = dict(payload)
        wrapped_payload.update(
            {
                "question_files": [FileCompat(file_obj) for file_obj in question_files],
                "answer_files": [FileCompat(file_obj) for file_obj in answer_files],
            }
        )
        if action == "save_question":
            return as_jsonable(save_question(wrapped_payload))
        if action == "save_combine":
            return as_jsonable(save_combine(wrapped_payload))
        if action == "save_anonym_question":
            return as_jsonable(save_anonym_question(wrapped_payload))
        return {"status": "error", "error_mess": "WARN: No valid action param"}, 200


@dataclass
class FileCompat:
    """Compatibility wrapper emulating the legacy Werkzeug `FileStorage` API."""

    source: UploadFile

    @property
    def filename(self) -> str | None:
        return self.source.filename

    def save(self, dst: str) -> None:
        path = Path(dst)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.source.file.seek(0)
        path.write_bytes(self.source.file.read())
