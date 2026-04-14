"""Framework-agnostic runtime config access helpers.

This module centralizes environment-based config resolution for code paths
that must work without Flask application context (e.g. Celery workers and
background integrations).
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.core.config import Config, DevConfig, ProdConfig
from app.core.env import get_env_bool


@lru_cache(maxsize=1)
def get_runtime_config_class() -> type[Config]:
    """Return active runtime config class based on current environment."""

    return ProdConfig if get_env_bool("PROD") else DevConfig


def get_config_value(key: str, default: Any = None) -> Any:
    """Read config value from active runtime config class."""

    return getattr(get_runtime_config_class(), key, default)
