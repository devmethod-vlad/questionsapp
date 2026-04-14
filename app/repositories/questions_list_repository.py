"""Repository helpers for `/questionslist/` read flow.

The legacy implementation mixed SQL text construction, execution and response
assembly in one module. This repository isolates database operations so the
service layer can focus on business orchestration and payload shaping.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import text

from questionsapp.models import Attachment, AnswerAttachment, OrderAttachment, OrderStatus, UserBaseRole
from questionsapp.services.auxillary.readsqltmpfile import read_sql_tmpfile


@dataclass(slots=True)
class SqlAlchemyQuestionsListRepository:
    """SQL-backed data access used by the native questions list service."""

    session: Any
    engine: Any

    def fetch_dataframe_records(self, *, query: str) -> list[dict[str, Any]]:
        """Execute SQL and return dataframe records represented as dictionaries."""

        dataframe = read_sql_tmpfile(query, self.engine)
        return dataframe.to_dict("records")

    def execute_scalar(self, *, query: str) -> int:
        """Run SQL and return first scalar value, defaulting to 0."""

        row = self.session.execute(text(query)).fetchone()
        if row is None:
            return 0
        return int(row[0] or 0)

    def execute_rows(self, *, query: str) -> list[tuple[Any, ...]]:
        """Run SQL and return all rows."""

        return list(self.session.execute(text(query)).fetchall())

    def get_order_status(self, *, order_id: int) -> OrderStatus | None:
        return OrderStatus.query.filter_by(orderid=order_id).first()

    def get_user_base_role(self, *, user_id: int) -> UserBaseRole | None:
        return UserBaseRole.query.filter_by(userid=user_id).first()

    def list_order_attachments(self, *, order_id: int) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for relation in OrderAttachment.query.filter_by(orderid=order_id).all():
            attach_rec = Attachment.query.filter_by(id=relation.attachid).first()
            if attach_rec is not None:
                result.append(
                    {
                        "type": attach_rec.type,
                        "path": attach_rec.path,
                        "attachid": attach_rec.id,
                        "public": attach_rec.public,
                    }
                )
        return result

    def list_answer_attachments(self, *, answer_id: int) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for relation in AnswerAttachment.query.filter_by(answerid=answer_id).all():
            attach_rec = Attachment.query.filter_by(id=relation.attachid).first()
            if attach_rec is not None:
                result.append(
                    {
                        "type": attach_rec.type,
                        "path": attach_rec.path,
                        "attachid": attach_rec.id,
                        "public": attach_rec.public,
                    }
                )
        return result
