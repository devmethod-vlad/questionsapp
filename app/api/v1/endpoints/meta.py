"""Operational and smoke-test endpoints."""

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

router = APIRouter()


@router.get("/test/", response_class=PlainTextResponse)
def test_endpoint() -> PlainTextResponse:
    """Keep legacy smoke test endpoint unchanged."""

    return PlainTextResponse("Test success!!!")
