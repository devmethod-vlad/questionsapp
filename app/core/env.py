"""Environment variable helpers for app runtime modules."""

from __future__ import annotations

import os
from typing import Optional


class MissingEnvironmentVariableError(RuntimeError):
    """Raised when a required environment variable is missing."""


def get_env(name: str, default: Optional[str] = None, *, required: bool = False) -> str:
    """Read environment variable with optional required validation."""

    value = os.getenv(name, default)

    if required and (value is None or value == ""):
        raise MissingEnvironmentVariableError(
            f"Required environment variable '{name}' is not set."
        )

    if value is None:
        return ""

    return value


def get_env_bool(name: str, default: bool = False) -> bool:
    """Read boolean environment variable with common truthy aliases."""

    value = os.getenv(name)
    if value is None:
        return default

    normalized = value.strip().lower()
    return normalized in {"1", "true", "yes", "y", "on"}

