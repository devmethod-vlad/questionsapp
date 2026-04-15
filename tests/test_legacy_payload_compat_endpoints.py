from __future__ import annotations

from dataclasses import dataclass

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.endpoints.questions import router as questions_router
from app.core.exceptions import register_exception_handlers
from app.db.session import get_request_session_context
from app.services.admin_service import AdminService
from app.services.dependencies import get_questions_service


@dataclass
class _DummySessionContext:
    session: object = object()


class StubQuestionsService:
    def get_questions_list(self, payload: dict):
        if not isinstance(payload.get("userid"), int) or payload.get("userid") == 0:
            return {"status": "error", "error_mess": "WARN: No params"}, 200
        if not isinstance(payload.get("roleid"), int):
            return {"status": "error", "error_mess": "WARN: No params"}, 200
        return {"status": "ok", "info": {"userid": payload.get("userid")}}, 200


def create_client(monkeypatch) -> TestClient:
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(questions_router, prefix="/eduportal/questions")
    app.dependency_overrides[get_questions_service] = lambda: StubQuestionsService()
    app.dependency_overrides[get_request_session_context] = lambda: _DummySessionContext()

    monkeypatch.setattr(AdminService, "get_space_roles", staticmethod(lambda payload, session: ({"status": "ok"}, 200)))
    def _service_action(payload, session):
        if payload.get("action") == "execaction":
            return {"status": "ok"}, 200
        return {"status": "error", "error_mess": "WARN: No valid action param"}, 200

    def _statistics(payload, session):
        return {"status": "ok"}, 200

    def _botexcel(payload):
        if payload.get("action") in {"getfollowersexcel", "getsuppinfo"}:
            return {"status": "ok"}, 200
        return {"status": "error", "error_mess": "WARN: No valid action param"}, 200

    monkeypatch.setattr(AdminService, "execute_service_action", staticmethod(_service_action))
    monkeypatch.setattr(AdminService, "get_statistics", staticmethod(_statistics))
    monkeypatch.setattr(AdminService, "build_bot_excel", staticmethod(_botexcel))
    return TestClient(app)


def test_questionslist_happy_path(monkeypatch) -> None:
    client = create_client(monkeypatch)
    response = client.post("/eduportal/questions/questionslist/", json={"userid": 1, "roleid": 2})
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_questionslist_missing_required_field(monkeypatch) -> None:
    client = create_client(monkeypatch)
    response = client.post("/eduportal/questions/questionslist/", json={"roleid": 2})
    assert response.status_code == 200
    assert response.json() == {"status": "error", "error_mess": "WARN: No params"}


def test_questionslist_invalid_type(monkeypatch) -> None:
    client = create_client(monkeypatch)
    response = client.post("/eduportal/questions/questionslist/", json={"userid": "bad", "roleid": 2})
    assert response.status_code == 200
    assert response.json() == {"status": "error", "error_mess": "WARN: No params"}


def test_questionslist_unknown_action_field_ignored(monkeypatch) -> None:
    client = create_client(monkeypatch)
    response = client.post(
        "/eduportal/questions/questionslist/",
        json={"userid": 1, "roleid": 2, "action": "unexpected_action"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_questionslist_empty_body_legacy_error(monkeypatch) -> None:
    client = create_client(monkeypatch)
    response = client.post("/eduportal/questions/questionslist/")
    assert response.status_code == 200
    assert response.json() == {"status": "error", "error_mess": "WARN: No params"}


def test_spaceandroles_compat_cases(monkeypatch) -> None:
    client = create_client(monkeypatch)

    assert client.post("/eduportal/questions/spaceandroles/", json={"action": "getrolesbyspace"}).json()["status"] == "ok"
    assert client.post("/eduportal/questions/spaceandroles/", json={}).json()["error_mess"] == "WARN: No action param"
    assert (
        client.post("/eduportal/questions/spaceandroles/", json={"action": {"nested": 1}}).json()["error_mess"]
        == "WARN: No valid action param"
    )
    assert (
        client.post("/eduportal/questions/spaceandroles/", json={"action": "unknown"}).json()["error_mess"]
        == "WARN: No valid action param"
    )
    assert client.post("/eduportal/questions/spaceandroles/").json()["error_mess"] == "WARN: No action param"


def test_service_compat_cases(monkeypatch) -> None:
    client = create_client(monkeypatch)

    assert client.post("/eduportal/questions/service/", json={"action": "execaction"}).json()["status"] == "ok"
    assert client.post("/eduportal/questions/service/", json={}).json()["error_mess"] == "WARN: No action param"
    assert client.post("/eduportal/questions/service/", json={"action": 0}).json()["error_mess"] == "WARN: No action param"
    assert (
        client.post("/eduportal/questions/service/", json={"action": "unknown"}).json()["error_mess"]
        == "WARN: No valid action param"
    )
    assert client.post("/eduportal/questions/service/").json()["error_mess"] == "WARN: No action param"


def test_statistic_compat_cases(monkeypatch) -> None:
    client = create_client(monkeypatch)

    assert (
        client.post(
            "/eduportal/questions/statistic/",
            json={"action": "getbotstat", "botstatskind": "newusers", "botimeperiod": 7},
        ).json()["status"]
        == "ok"
    )
    assert client.post("/eduportal/questions/statistic/", json={}).json()["error_mess"] == "WARN: No action param"
    assert (
        client.post(
            "/eduportal/questions/statistic/",
            json={"action": "getbotstat", "botstatskind": "newusers", "botimeperiod": "7"},
        ).json()["error_mess"]
        == "WARN: No params"
    )
    assert (
        client.post("/eduportal/questions/statistic/", json={"action": "unknown"}).json()["error_mess"]
        == "WARN: No valid action param"
    )
    assert (
        client.post(
            "/eduportal/questions/statistic/",
            json={"action": "getbotstat", "botimeperiod": 7},
        ).json()["error_mess"]
        == "WARN: No params"
    )


def test_botexcel_compat_cases(monkeypatch) -> None:
    client = create_client(monkeypatch)

    assert (
        client.post(
            "/eduportal/questions/botexcel/",
            json={"action": "getfollowersexcel", "chatid": 42},
        ).json()["status"]
        == "ok"
    )
    assert client.post("/eduportal/questions/botexcel/", json={}).json()["error_mess"] == "WARN: No params"
    assert (
        client.post(
            "/eduportal/questions/botexcel/",
            json={"action": "getfollowersexcel", "chatid": []},
        ).json()["status"]
        == "ok"
    )
    assert (
        client.post("/eduportal/questions/botexcel/", json={"action": "unknown", "chatid": 1}).json()["error_mess"]
        == "WARN: No valid action param"
    )
    assert client.post("/eduportal/questions/botexcel/").json()["error_mess"] == "WARN: No params"
