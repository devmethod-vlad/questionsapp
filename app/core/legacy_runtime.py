"""Legacy runtime compatibility helpers without Flask app-context dependency."""

from __future__ import annotations

from app.core.config import DevConfig, ProdConfig
from questionsapp.env import get_env_bool


class LegacyAppProxy:
    """Tiny `current_app` replacement for legacy modules.

    Legacy code frequently accesses ``app.config[...]`` / ``app.config.get(...)``.
    This proxy provides the same lookup surface using FastAPI-era config classes,
    so legacy business modules can run without creating a Flask app instance.
    """

    def __init__(self) -> None:
        self._config_cls = ProdConfig if get_env_bool("PROD") else DevConfig

    @property
    def config(self) -> "LegacyAppProxy":
        return self

    def __getitem__(self, key: str):
        return getattr(self._config_cls, key)

    def get(self, key: str, default=None):
        return getattr(self._config_cls, key, default)


app = LegacyAppProxy()
