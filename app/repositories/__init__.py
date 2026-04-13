"""Repository and data-access abstractions for FastAPI layer."""

from app.repositories.legacy_session import LegacySessionContext, get_legacy_session_context

__all__ = ["LegacySessionContext", "get_legacy_session_context"]
