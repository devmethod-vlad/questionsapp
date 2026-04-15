import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("PG_CONTAINER", "localhost")
os.environ.setdefault("PG_BASE", "test")
os.environ.setdefault("QUESTIONS_ATTACHMENTS", "/tmp")

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.endpoints.questions import router
from app.core.exceptions import register_exception_handlers
from app.core.rate_limit import questions_api_limiter
from app.services.dependencies import get_questions_service


class _OkService:
    def get_public_questions(self, *, page, page_count, public_only):
        assert page == "1"
        assert page_count == "100"
        assert public_only is False
        return ([{"id": 1}], 1)


class _ValidationService:
    def get_public_questions(self, *, page, page_count, public_only):
        int(page)
        int(page_count)
        return ([], 0)


class _FailService:
    def get_public_questions(self, *, page, page_count, public_only):
        raise RuntimeError("db down")


def _build_client(service) -> TestClient:
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(router)

    @app.get("/health")
    def healthcheck():
        return {"status": "ok"}

    app.dependency_overrides[get_questions_service] = lambda: service
    return TestClient(app)


def setup_function() -> None:
    questions_api_limiter.reset()


def test_questions_api_happy_path_returns_paginated_payload():
    client = _build_client(_OkService())

    response = client.get("/questions_api/", params={"extra_data": ""})

    assert response.status_code == 200
    assert response.json() == {
        "count": 1,
        "page_count": 1,
        "page": 1,
        "data": [{"id": 1}],
    }


def test_questions_api_invalid_page_returns_legacy_400_error():
    client = _build_client(_ValidationService())

    response = client.get("/questions_api/", params={"page": "abc", "extra_data": ""})

    assert response.status_code == 400
    assert response.json() == {
        "status": "error",
        "error_mess": "Invalid pagination parameters; must be integers.",
    }


def test_questions_api_invalid_page_count_returns_legacy_400_error():
    client = _build_client(_ValidationService())

    response = client.get("/questions_api/", params={"page_count": "abc", "extra_data": ""})

    assert response.status_code == 400
    assert response.json() == {
        "status": "error",
        "error_mess": "Invalid pagination parameters; must be integers.",
    }


def test_questions_api_internal_error_returns_legacy_500_error_message():
    client = _build_client(_FailService())

    response = client.get("/questions_api/", params={"extra_data": ""})

    assert response.status_code == 500
    assert response.json() == {
        "status": "error",
        "error_mess": "Internal server error while fetching data.",
    }


def test_questions_api_rate_limit_allows_60_requests_and_blocks_61st():
    client = _build_client(_OkService())

    for _ in range(60):
        response = client.get("/questions_api/", params={"extra_data": ""})
        assert response.status_code == 200

    response = client.get("/questions_api/", params={"extra_data": ""})

    assert response.status_code == 429
    assert response.json() == {"detail": "60 per minute"}


def test_questions_api_rate_limit_does_not_affect_other_endpoints():
    client = _build_client(_OkService())

    for _ in range(61):
        client.get("/questions_api/", params={"extra_data": ""})

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
