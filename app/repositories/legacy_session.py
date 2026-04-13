"""Legacy SQLAlchemy session lifecycle helpers for FastAPI requests.

Step 5 migration target:
- explicit session dependency via ``Depends``;
- deterministic cleanup under ASGI worker lifecycle;
- rollback safety if an exception occurs before legacy service commits.
"""

from __future__ import annotations

from collections.abc import Generator

from database import db


class LegacySessionContext:
    """Small helper to keep session lifecycle actions centralized."""

    def rollback(self) -> None:
        db.session.rollback()

    def remove(self) -> None:
        db.session.remove()


def get_legacy_session_context() -> Generator[LegacySessionContext, None, None]:
    """FastAPI dependency that provides per-request legacy session context."""

    context = LegacySessionContext()
    try:
        yield context
    except Exception:
        context.rollback()
        raise
    finally:
        context.remove()
