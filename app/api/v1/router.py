"""Top-level API router with domain-level route composition."""

from fastapi import APIRouter

from app.api.v1.endpoints.meta import router as meta_router
from app.api.v1.endpoints.questions import router as questions_router

api_router = APIRouter()
api_router.include_router(meta_router)
api_router.include_router(questions_router)
