"""Native SQLAlchemy engine and session factory for FastAPI runtime.

This module is intentionally framework-agnostic: it does not import Flask or
Flask-SQLAlchemy and can be reused by HTTP handlers, background workers and
repository code.
"""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from app.core.config import Config

_ENGINE = create_engine(
    Config.SQLALCHEMY_DATABASE_URI,
    **Config.SQLALCHEMY_ENGINE_OPTIONS,
)

SessionFactory = scoped_session(
    sessionmaker(
        bind=_ENGINE,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )
)


def get_engine():
    """Return singleton SQLAlchemy engine used by native runtime paths."""

    return _ENGINE
