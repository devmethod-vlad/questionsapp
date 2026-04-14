"""Status conversion helper used by legacy request-processing code."""

from __future__ import annotations

from app.core.runtime_config import get_question_statuses

def tranform_status_list(status_name_list):
    status_id_list = []
    question_statuses = get_question_statuses()

    for item in status_name_list:
        if item in question_statuses:
            status_id_list.append(question_statuses[item]["id"])

    return status_id_list
