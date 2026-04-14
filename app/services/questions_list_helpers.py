"""Pure helpers for `/questionslist/` request normalization and SQL snippets."""

from __future__ import annotations

from typing import Any


def divide_chunks(items: list[int], size: int):
    for index in range(0, len(items), size):
        yield items[index : index + size]


def validate_questions_list_params(params: dict[str, Any]) -> bool:
    if not params.get("userid") or int(params["userid"]) == 0:
        return False
    if not params.get("roleid") or int(params["roleid"]) == 0:
        return False

    int_fields = ["spaceid", "statusid", "perpagecount", "activepage", "enablesearch", "forsynchroflag"]
    str_fields = ["searchinput", "usertoken"]

    for field in int_fields:
        if not isinstance(params.get(field), int):
            return False

    for field in str_fields:
        if not isinstance(params.get(field), str):
            return False

    return True


def is_numeric_search(params: dict[str, Any]) -> bool:
    return int(params["enablesearch"]) == 1 and params["searchinput"] != "" and params["searchinput"].isnumeric()


def build_status_condition(
    *,
    role: str,
    user_id: int,
    status_keys: list[str],
    question_statuses: dict[str, dict[str, Any]],
    is_numeric: bool = False,
) -> str:
    status_ids = [question_statuses[key]["id"] for key in status_keys]

    if role == "redactor" and "trash" in status_keys:
        condition = " and (" if is_numeric else " and "
        for idx, status_id in enumerate(status_ids):
            if status_id == question_statuses["trash"]["id"]:
                condition += f" (stord.id={status_id} and ordermess.userid={user_id})"
            else:
                condition += f" stord.id={status_id}"
            if idx != len(status_ids) - 1:
                condition += " or"
        if is_numeric:
            condition += ")"
        return condition

    return " and stord.id in (" + ",".join(str(status_id) for status_id in status_ids) + ")"


def build_query_conditions(
    *,
    numeric_search: bool,
    role: str,
    params: dict[str, Any],
    question_statuses: dict[str, dict[str, Any]],
    default_render_statuses: list[str],
) -> dict[str, str]:
    all_statuses = ["create", "inwork", "received_answer", "archive", "trash", "back_in_work"]

    if role in {"redactor", "admin"} and int(params["isfeedback"]) == 1 and not numeric_search and int(params["showonlypublic"]) != 1:
        feedback_condition = " where fq.orderid is NOT NULL "
    else:
        feedback_condition = " where fq.orderid is NULL "

    public_condition = " and ordpublic is not NULL " if int(params["showonlypublic"]) == 1 else ""

    search_condition = ""
    if params["searchinput"].strip() != "":
        if numeric_search:
            search_condition = f" and ordermess.id={params['searchinput']}"
        else:
            search_condition = f" and ordermess.text ilike '%{params['searchinput'].lower()}%'"

    if int(params["isfeedback"]) == 1:
        status_condition = f" and stord.id={question_statuses['archive']['id']}"
    elif int(params["showonlypublic"]) == 1:
        status_condition = build_status_condition(
            role=role,
            user_id=params["userid"],
            status_keys=["received_answer", "archive", "back_in_work"],
            question_statuses=question_statuses,
        )
    elif int(params["statusid"]) == 0:
        if numeric_search or params["searchinput"].strip() != "":
            status_condition = build_status_condition(
                role=role,
                user_id=params["userid"],
                status_keys=all_statuses,
                question_statuses=question_statuses,
                is_numeric=True,
            )
        else:
            status_condition = build_status_condition(
                role=role,
                user_id=params["userid"],
                status_keys=default_render_statuses,
                question_statuses=question_statuses,
            )
    else:
        status_condition = f" and stord.id={params['statusid']}"
        if role == "redactor" and int(params["statusid"]) == question_statuses["trash"]["id"]:
            status_condition = f" and (stord.id={params['statusid']} and ordermess.userid={params['userid']})"

    space_condition = ""
    if not numeric_search and params["searchinput"].strip() == "" and int(params["spaceid"]) != 0:
        space_condition = f" and space.id={params['spaceid']}"

    role_condition = f" and ordermess.userid={params['userid']}" if role == "personal" else ""

    orderby_condition = ""
    if not numeric_search:
        sort = params["datesort"]
        if sort == "asc":
            orderby_condition = " order by ordermess.created_at asc, ordermess.text asc "
        elif sort == "desc":
            orderby_condition = " order by ordermess.created_at desc, ordermess.text asc "
        elif sort == "notset":
            orderby_condition = " order by ordermess.text desc "
        else:
            orderby_condition = " order by ordermess.created_at desc, ordermess.text asc "

    return {
        "search_condition": search_condition,
        "status_condition": status_condition,
        "space_condition": space_condition,
        "role_condition": role_condition,
        "orderby_condition": orderby_condition,
        "feedback_condition": feedback_condition,
        "public_condition": public_condition,
    }


def build_limit_condition(*, numeric_search: bool, params: dict[str, Any]) -> str:
    if numeric_search:
        return ""
    offset = (int(params["activepage"]) - 1) * int(params["perpagecount"])
    if offset == 0:
        return f" limit {params['perpagecount']}"
    return f" limit {params['perpagecount']} offset {offset}"
