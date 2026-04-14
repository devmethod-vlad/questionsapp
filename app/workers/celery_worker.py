"""Celery worker bootstrap without Flask app factory dependency."""

from __future__ import annotations

import os

from celery import Celery

from app.core.runtime_config import get_runtime_config_class


def _runtime_config_dict() -> dict[str, object]:
    """Export uppercase config attributes for Celery runtime config."""

    config = get_runtime_config_class()
    return {
        key: value
        for key, value in vars(config).items()
        if key.isupper()
    }


celery = Celery(
    "questionsapp",
    backend=os.getenv("CELERY_RESULT_BACKEND"),
    broker=os.getenv("CELERY_BROKER_URL"),
)
celery.conf.update(_runtime_config_dict())
celery.autodiscover_tasks(["app.workers.tasks"])

