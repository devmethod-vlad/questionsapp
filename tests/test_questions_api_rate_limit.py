from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.endpoints.meta import router as meta_router
from app.api.v1.endpoints.questions import router as questions_router
from app.core.rate_limit import questions_api_rate_limit
from app.services.dependencies import get_questions_service


class StubQuestionsService:
    def get_public_questions(self, *, page: int, page_count: int, public_only: bool):
        data = [
            {
                "id": 1,
                "orderid": 100,
                "question": "Q",
                "answer": "A",
                "publicorder": 1 if public_only else 0,
            }
        ]
        return data[: int(page_count)], 1


def create_client() -> TestClient:
    app = FastAPI()
    app.include_router(meta_router, prefix="/eduportal/questions")
    app.include_router(questions_router, prefix="/eduportal/questions")
    app.dependency_overrides[get_questions_service] = lambda: StubQuestionsService()
    return TestClient(app)


def test_questions_api_rate_limit_triggers_on_61st_request() -> None:
    questions_api_rate_limit.reset()
    client = create_client()

    for _ in range(60):
        response = client.get("/eduportal/questions/questions_api/?extra_data=1")
        assert response.status_code == 200

    limited = client.get("/eduportal/questions/questions_api/?extra_data=1")
    assert limited.status_code == 429
    assert limited.json() == {"detail": "Too Many Requests"}


def test_rate_limit_not_applied_to_neighbor_endpoint() -> None:
    questions_api_rate_limit.reset()
    client = create_client()

    for _ in range(61):
        _ = client.get("/eduportal/questions/questions_api/?extra_data=1")

    test_endpoint_response = client.get("/eduportal/questions/test/")
    assert test_endpoint_response.status_code == 200
    assert test_endpoint_response.text == "Test success!!!"
