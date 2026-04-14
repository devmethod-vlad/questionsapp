"""Celery worker bootstrap without Flask app factory dependency."""

from __future__ import annotations

from celery import Celery

from app.core.settings import get_settings


def _runtime_config_dict() -> dict[str, object]:
    """Export compatibility runtime config mapping for Celery."""

    return get_settings().runtime_config_dict()


celery = Celery(
    "questionsapp",
    backend=get_settings().celery_result_backend,
    broker=get_settings().celery_broker_url,
)
celery.conf.update(_runtime_config_dict())
celery.autodiscover_tasks(["app.workers.tasks"])

