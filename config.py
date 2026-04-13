"""Backward-compatible config module.

Legacy imports (`config.DevConfig`, `config.ProdConfig`) are kept for
transitional compatibility, but canonical definitions now live in
`app.core.config`.
"""

from app.core.config import Config, DevConfig, ProdConfig

__all__ = ["Config", "ProdConfig", "DevConfig"]
