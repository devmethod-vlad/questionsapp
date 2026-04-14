"""Compatibility export for legacy-style ``db.session`` access.

Active FastAPI runtime now uses native SQLAlchemy session management from
:mod:`app.db.engine`. This shim keeps old modules functional while migration is
in progress, but no longer relies on ``database.py``/Flask-SQLAlchemy.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.db.engine import SessionFactory


@dataclass(frozen=True)
class _LegacyDbAdapter:
    """Small adapter exposing ``session`` to legacy modules."""

    @property
    def session(self):
        return SessionFactory()


# Legacy import style: ``from app.db.legacy_db import db``
db = _LegacyDbAdapter()

__all__ = ["db"]
