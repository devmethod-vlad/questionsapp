"""Repositories for question read operations.

Repository layer isolates SQL from API handlers/services so the data-access
strategy can evolve independently from HTTP endpoints.
"""

from __future__ import annotations

from typing import Protocol

from sqlalchemy import text


class QuestionsReadRepository(Protocol):
    """Read-only repository contract for question API feed."""

    def get_public_questions(self, *, page: int, page_count: int, public_only: bool, url_prefix: str) -> tuple[list[dict], int]:
        """Return paginated questions and total count."""


class SqlAlchemyQuestionsReadRepository:
    """SQLAlchemy implementation preserving the legacy SQL contract."""

    def __init__(self, session):
        self._session = session

    def get_public_questions(self, *, page: int, page_count: int, public_only: bool, url_prefix: str) -> tuple[list[dict], int]:
        attach_orders_base = f"https://edu.emias.ru{url_prefix}/static/attachments/orders"
        attach_answers_base = f"https://edu.emias.ru{url_prefix}/static/attachments/answers"

        public_clause = "AND order_public.orderid IS NOT NULL" if public_only else ""

        base_sql = f"""
            FROM ordermess ord
            JOIN order_status ON ord.id = order_status.orderid
            JOIN statusorder ON statusorder.id = order_status.statusid
            LEFT JOIN order_infospace ON order_infospace.orderid = ord.id
            LEFT JOIN infospace ON infospace.id = order_infospace.spaceid
            LEFT JOIN order_unionrole ON order_unionrole.orderid = ord.id
            LEFT JOIN unionrole ON unionrole.id = order_unionrole.unionroleid
            LEFT JOIN order_public ON order_public.orderid = ord.id
            LEFT JOIN order_attachment ord_att ON ord_att.orderid = ord.id
            LEFT JOIN attachment order_attach ON order_attach.id = ord_att.attachid
            JOIN answermess answ ON answ.orderid = ord.id
            LEFT JOIN answer_attachment answ_att ON answ_att.answerid = answ.id
            LEFT JOIN attachment answer_attach ON answer_attach.id = answ_att.attachid
            WHERE answ.id IS NOT NULL
              AND statusorder.id IN (4)
              {public_clause}
        """

        data_query_sql = f"""
            SELECT
                ord.id AS id,
                infospace.title AS space,
                unionrole.name AS role,
                unionrole.emiasid AS role_id,
                CASE WHEN order_public.id IS NOT NULL THEN true ELSE false END AS public,
                ord.text AS question,
                array_agg(
                    DISTINCT CAST(:attach_orders_base AS text) || '/' || COALESCE(ord.userid::text, '') || '/'
                            || COALESCE(ord.id::text, '') || '/' || COALESCE(order_attach.path, '')
                ) FILTER (WHERE order_attach.path IS NOT NULL AND order_attach.public = 1) AS question_attach,
                answ.text AS answer,
                array_agg(
                    DISTINCT CAST(:attach_answers_base AS text) || '/' || COALESCE(ord.userid::text, '') || '/'
                            || COALESCE(ord.id::text, '') || '/' || COALESCE(answer_attach.path, '')
                ) FILTER (WHERE answer_attach.path IS NOT NULL AND answer_attach.public = 1) AS answer_attach,
                to_char(
                    (
                        GREATEST(
                            COALESCE(MAX(ord.modified_at),  'epoch'::timestamptz),
                            COALESCE(MAX(answ.modified_at), 'epoch'::timestamptz)
                        ) AT TIME ZONE 'Europe/Moscow'
                    ),
                    'YYYY-MM-DD"T"HH24:MI:SS.MS'
                ) || '+03:00' AS modified_at
            {base_sql}
            GROUP BY ord.id, ord.modified_at, infospace.title, unionrole.name, unionrole.emiasid, ord.text, answ.text, answ.modified_at, order_public.id
            ORDER BY ord.id
            LIMIT :limit OFFSET :offset
        """

        count_query_sql = f"SELECT COUNT(DISTINCT ord.id) {base_sql}"
        params = {
            "limit": page_count,
            "offset": (page - 1) * page_count,
            "attach_orders_base": attach_orders_base,
            "attach_answers_base": attach_answers_base,
        }

        result = self._session.execute(text(data_query_sql), params)
        rows = result.fetchall()
        total_count = self._session.execute(text(count_query_sql)).scalar()

        columns = list(result.keys())
        data: list[dict] = []
        for row in rows:
            record = dict(zip(columns, row))
            for field in ("question_attach", "answer_attach"):
                values = record.get(field)
                record[field] = [value for value in values if value] if values else []
            data.append(record)

        return data, int(total_count or 0)
