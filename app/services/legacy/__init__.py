"""Service-level temporary adapters used during Flask -> FastAPI migration."""

from app.services.legacy.admin_handlers import LegacyAdminHandlers
from app.services.legacy.question_handlers import LegacyQuestionHandlers

__all__ = ["LegacyAdminHandlers", "LegacyQuestionHandlers"]
