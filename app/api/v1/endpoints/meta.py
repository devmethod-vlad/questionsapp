"""Operational and smoke-test endpoints."""

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

router = APIRouter()


@router.get("/test/")
def test_endpoint() -> PlainTextResponse:
    """Keep legacy smoke test endpoint unchanged."""

    return PlainTextResponse("Test success!!!")
