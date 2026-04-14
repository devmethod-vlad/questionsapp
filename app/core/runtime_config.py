"""Runtime accessors for migration-safe legacy configuration values.

This module provides framework-agnostic access to configuration constants that
were historically read from ``flask.current_app.config``.

The goal is to keep business behavior identical while removing hard dependency
on Flask application context in native FastAPI runtime paths.
"""

from __future__ import annotations

from typing import Any

from app.core.config import BASE_ROLE, NULLROLE, NULLSPACE, QUESTION_STATUS, URL_PREFIX


def get_base_roles() -> dict[str, dict[str, Any]]:
    """Return role mapping used by legacy role-related helpers."""

    return BASE_ROLE


def get_question_statuses() -> dict[str, dict[str, Any]]:
    """Return status mapping used across question workflows."""

    return QUESTION_STATUS


def get_null_space() -> dict[str, Any]:
    """Return placeholder space metadata used by question flows."""

    return NULLSPACE


def get_null_role() -> dict[str, Any]:
    """Return placeholder role metadata used by question flows."""

    return NULLROLE


def get_url_prefix() -> str:
    """Return URL prefix used by legacy-compatible API response fields."""

    return URL_PREFIX
