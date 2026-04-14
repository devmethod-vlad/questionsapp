"""Native application service for `/questionslist/`.

This service preserves the legacy response envelope/fields while removing
runtime coupling to Flask app context and per-call engine construction.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from app.core.constants import (
    DEFAULT_RENDER_STATUSES,
    NULLROLE,
    NULLSPACE,
    QUESTION_STATUS,
    SHOW_ALL_SPACES_ITEM,
)
from app.repositories.auth_repository import SqlAlchemyAuthRepository
from app.repositories.questions_list_repository import SqlAlchemyQuestionsListRepository
from app.services.legacy.roles.getrole import get_role
from app.services.questions_list_helpers import (
    build_limit_condition,
    build_query_conditions,
    build_status_condition,
    divide_chunks,
    is_numeric_search,
    validate_questions_list_params,
)
from app.services.auth.user_token_service import check_user_token
from supp_db.queries.questions import (
    ALL_SPACES_QUERY,
    feedback_query,
    public_query,
    select_count,
    select_status,
    sql_find_question,
    sql_questions,
    sql_questions_service,
)


@dataclass(slots=True)
class QuestionsListService:
    """Service that orchestrates `questionslist` SQL and payload shaping."""

    repository: SqlAlchemyQuestionsListRepository

    def find_question_in_list(self, params: dict[str, Any]) -> dict[str, Any]:
        list_params = {
            "statusId": 0,
            "spaceId": 0,
            "activePage": 1,
            "countPerPage": 5,
            "sorting": "desc",
            "searchInput": "",
            "enableSearch": 0,
        }

        if not params.get("userid") or not params.get("orderid"):
            return {"status": "error", "error_mess": "WARN: No params"}

        try:
            user_id = int(params["userid"])
            order_id = int(params["orderid"])
            order_status = self.repository.get_order_status(order_id=order_id)
            user_role = self.repository.get_user_base_role(user_id=user_id)
            if order_status is None or user_role is None:
                return {"status": "ok", "info": list_params}

            role = get_role(user_role.roleid)
            role_condition = ""
            if role == "personal" or (role == "redactor" and order_status.statusid == QUESTION_STATUS["trash"]["id"]):
                role_condition = f" and ordermess.userid={user_id}"

            query = f"{sql_find_question} where os.statusid={order_status.statusid} {role_condition}"
            records = self.repository.fetch_dataframe_records(query=query)
            if records:
                question_ids = [int(item["id"]) for item in records]
                if order_id in question_ids:
                    list_params["statusId"] = order_status.statusid
                    if len(question_ids) > 5:
                        for page_index, chunk in enumerate(divide_chunks(question_ids, 5), start=1):
                            if order_id in chunk:
                                list_params["activePage"] = page_index
                                break
        except Exception as exc:  # pragma: no cover - legacy-compatible envelope
            print(str(exc))

        return {"status": "ok", "info": list_params}

    def form_questions_list(self, params: dict[str, Any]) -> dict[str, Any]:
        if not validate_questions_list_params(params):
            return {"status": "error", "error_mess": "WARN: No params"}

        question_statuses = QUESTION_STATUS
        if int(params["statusid"]) == int(question_statuses["public"]["id"]):
            params["statusid"] = 0

        role = get_role(params["roleid"])
        numeric_search = is_numeric_search(params)
        conditions = build_query_conditions(
            numeric_search=numeric_search,
            role=role,
            params=params,
            question_statuses=question_statuses,
            default_render_statuses=DEFAULT_RENDER_STATUSES,
        )

        limit_condition = build_limit_condition(numeric_search=numeric_search, params=params)

        result_query = (
            sql_questions
            + conditions["feedback_condition"]
            + conditions["public_condition"]
            + conditions["status_condition"]
            + conditions["space_condition"]
            + conditions["search_condition"]
            + conditions["role_condition"]
            + conditions["orderby_condition"]
            + limit_condition
        )

        count_query = (
            select_count
            + sql_questions_service
            + conditions["feedback_condition"]
            + conditions["public_condition"]
            + conditions["status_condition"]
            + conditions["space_condition"]
            + conditions["search_condition"]
            + conditions["role_condition"]
        )
        count_by_conditions = self.repository.execute_scalar(query=count_query)

        feedback_count = 0
        if role in {"admin", "redactor"}:
            feedback_count = self.repository.execute_scalar(query=select_count + feedback_query)

        public_count = self.repository.execute_scalar(query=select_count + public_query + conditions["role_condition"])

        all_status_keys = ["create", "inwork", "received_answer", "archive", "trash", "back_in_work"]
        all_statuses_query = (
            select_status
            + sql_questions_service
            + " where fq.orderid is NULL "
            + build_status_condition(
                role=role,
                user_id=params["userid"],
                status_keys=all_status_keys,
                question_statuses=question_statuses,
            )
            + conditions["role_condition"]
        )

        available_statuses = [
            {"id": row[0], "name": row[1]} for row in self.repository.execute_rows(query=all_statuses_query)
        ]
        if available_statuses:
            available_statuses = sorted(available_statuses, key=lambda item: item["id"])

        if feedback_count > 0:
            available_statuses.append(
                {"id": question_statuses["feedback"]["id"], "name": question_statuses["feedback"]["name"]}
            )
        if public_count > 0:
            available_statuses.append({"id": question_statuses["public"]["id"], "name": question_statuses["public"]["name"]})

        available_spaces = [
            {"id": row[0], "title": row[1], "spacekey": row[2]} for row in self.repository.execute_rows(query=ALL_SPACES_QUERY)
        ]

        null_space = NULLSPACE
        if not any(item["spacekey"] == null_space["spacekey"] for item in available_spaces):
            available_spaces.append(
                {"id": null_space["id"], "title": null_space["title"], "spacekey": null_space["spacekey"]}
            )

        if available_spaces:
            available_spaces = sorted(available_spaces, key=lambda item: item["title"])

        available_spaces.insert(0, SHOW_ALL_SPACES_ITEM)

        all_count_query = (
            select_count
            + sql_questions_service
            + build_status_condition(
                role=role,
                user_id=params["userid"],
                status_keys=all_status_keys,
                question_statuses=question_statuses,
            )
            + conditions["role_condition"]
        )
        total_count = self.repository.execute_scalar(query=all_count_query)

        result_list = self._process_records(self.repository.fetch_dataframe_records(query=result_query))
        for item in result_list:
            self._add_default_front_params(item)
            self._attach_files(item)

        info_object: dict[str, Any] = {
            "render_list": result_list,
            "total_count_by_conditions": count_by_conditions,
            "total_count": total_count,
            "available_statuses": available_statuses,
            "available_spaces": available_spaces,
        }

        if int(params["forsynchroflag"]) == 1:
            auth_repository = SqlAlchemyAuthRepository(session=self.repository.session)
            token_check = check_user_token(params["usertoken"], repository=auth_repository)
            info_object["user_token_status"] = token_check["status"]

        return {"status": "ok", "info": info_object}

    @staticmethod
    def _process_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not records:
            return []

        dataframe = pd.DataFrame(records)
        null_role = NULLROLE
        dataframe["order_unionrole_id"] = dataframe["order_unionrole_id"].fillna(null_role["id"])
        dataframe["order_unionrole_name"] = dataframe["order_unionrole_name"].fillna(null_role["name"])
        dataframe["order_unionrole_emiasid"] = dataframe["order_unionrole_emiasid"].fillna(null_role["emiasid"])
        dataframe["answer_id"] = dataframe["answer_id"].fillna(0)
        dataframe = dataframe.replace(np.nan, None)
        dataframe["order_created_at"] = pd.to_datetime(dataframe["order_created_at"], format="mixed")
        dataframe["order_created_at"] = dataframe["order_created_at"].dt.strftime("%d.%m.%Y %H:%M")
        return dataframe.to_dict("records")

    @staticmethod
    def _add_default_front_params(item: dict[str, Any]) -> None:
        item["order_union_roles"] = []
        item["new_order_upload_files"] = []
        item["deny_order_upload_files"] = []
        item["upload_order_infoarray"] = []
        item["order_simul_files"] = 0
        item["new_answer_upload_files"] = []
        item["deny_answer_upload_files"] = []
        item["upload_answer_infoarray"] = []
        item["answer_simul_files"] = 0
        item["is_update_active"] = 0

    def _attach_files(self, item: dict[str, Any]) -> None:
        item["order_attachments"] = self.repository.list_order_attachments(order_id=int(item["order_id"]))
        answer_id = int(item["answer_id"])
        item["answer_attachments"] = [] if answer_id == 0 else self.repository.list_answer_attachments(answer_id=answer_id)
