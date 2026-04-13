"""Backward-compatible import shim for migrated question API query service."""

from app.services.legacy.questions.get_questions_api import *  # noqa: F401,F403
