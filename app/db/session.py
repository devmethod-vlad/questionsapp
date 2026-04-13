"""Request-scoped database lifecycle management for FastAPI.

This module is the single source of truth for DB session handling in HTTP
request flow. It centralizes rollback/remove policy and gives repositories a
consistent session dependency.
"""

from __future__ import annotations

from collections.abc import Generator

from database import db


class RequestSessionContext:
    """Lightweight wrapper around the legacy Flask-SQLAlchemy scoped session."""

    @property
    def session(self):
        """Expose active SQLAlchemy session for repositories/services."""

        return db.session

    def rollback(self) -> None:
        """Rollback current transaction for unhandled request errors."""

        db.session.rollback()

    def remove(self) -> None:
        """Remove scoped session to prevent session leakage across requests."""

        db.session.remove()


def get_request_session_context() -> Generator[RequestSessionContext, None, None]:
    """Provide request-scoped session context with deterministic cleanup."""

    context = RequestSessionContext()
    try:
        yield context
    except Exception:
        context.rollback()
        raise
    finally:
        context.remove()
