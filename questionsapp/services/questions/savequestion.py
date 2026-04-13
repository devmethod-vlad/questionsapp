"""Backward-compatible import shim for migrated save_question service."""

from app.services.legacy.questions.savequestion import *  # noqa: F401,F403
