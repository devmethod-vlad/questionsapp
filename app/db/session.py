"""Request-scoped database lifecycle management for FastAPI.

This module is the single source of truth for DB session handling in HTTP
request flow. It centralizes rollback/remove policy and gives repositories a
consistent session dependency.
"""

from __future__ import annotations

from collections.abc import Generator

from app.db.engine import SessionFactory


class RequestSessionContext:
    """Request-level SQLAlchemy session holder.

    A new session is materialized lazily from ``SessionFactory`` and cleaned up
    by the dependency lifecycle in :func:`get_request_session_context`.
    """

    def __init__(self) -> None:
        self._session = SessionFactory()

    @property
    def session(self):
        """Expose active SQLAlchemy session for repositories/services."""

        return self._session

    def rollback(self) -> None:
        """Rollback current transaction for unhandled request errors."""

        self._session.rollback()

    def remove(self) -> None:
        """Remove scoped session to prevent session leakage across requests."""

        SessionFactory.remove()


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
