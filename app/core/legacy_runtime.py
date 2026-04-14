"""Framework-agnostic legacy runtime helpers.

This module provides lightweight compatibility objects that mirror the tiny
subset of Flask runtime API (`current_app.config`) still expected by migrated
legacy handlers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.config import DevConfig, ProdConfig
from app.core.env import get_env_bool


def _build_runtime_config() -> dict[str, Any]:
    """Build immutable config snapshot matching legacy Flask config values."""

    config_class = ProdConfig if get_env_bool("PROD") else DevConfig
    return {
        key: getattr(config_class, key)
        for key in dir(config_class)
        if key.isupper()
    }


@dataclass(frozen=True, slots=True)
class LegacyAppProxy:
    """Minimal drop-in replacement for ``current_app`` config reads."""

    config: dict[str, Any]


legacy_app = LegacyAppProxy(config=_build_runtime_config())
