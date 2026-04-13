"""Domain-grouped endpoint routers for migration step 4.x."""

from app.api.v1.endpoints.meta import router as meta_router
from app.api.v1.endpoints.questions import router as questions_router

__all__ = ["meta_router", "questions_router"]
