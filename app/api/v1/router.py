from fastapi import APIRouter

from app.api.v1.endpoints import router as legacy_router

api_router = APIRouter()
api_router.include_router(legacy_router)
