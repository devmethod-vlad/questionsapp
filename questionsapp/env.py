import os
from typing import Optional


class MissingEnvironmentVariableError(RuntimeError):
    """Raised when a required environment variable is missing."""


def get_env(name: str, default: Optional[str] = None, *, required: bool = False) -> str:
    value = os.getenv(name, default)

    if required and (value is None or value == ""):
        raise MissingEnvironmentVariableError(
            f"Required environment variable '{name}' is not set."
        )

    if value is None:
        return ""

    return value


def get_env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default

    normalized = value.strip().lower()
    return normalized in {"1", "true", "yes", "y", "on"}


def get_env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(
            f"Environment variable '{name}' must be an integer, got: '{value}'."
        ) from exc
