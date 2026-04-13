"""Backward-compatible import shim for request DB lifecycle dependency.

Use :mod:`app.db.session` in new code.
"""

from app.db.session import RequestSessionContext, get_request_session_context

# Backward compatibility names used by existing routers.
LegacySessionContext = RequestSessionContext
get_legacy_session_context = get_request_session_context
