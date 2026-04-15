from __future__ import annotations

from dataclasses import dataclass

from app.services.web_service import WebService


@dataclass
class StubWebRepository:
    order_exists_result: bool = False
    anonym_order_exists_result: bool = False
    last_order_id: int | None = None

    def has_telegram_user(self, *, telegram_id: str) -> bool:
        return False

    def order_exists(self, *, order_id: int) -> bool:
        self.last_order_id = order_id
        return self.order_exists_result

    def anonym_order_exists(self, *, order_id: int) -> bool:
        self.last_order_id = order_id
        return self.anonym_order_exists_result


def test_is_invalid_anonym_viewer_request_when_param_missing():
    service = WebService(repository=StubWebRepository())

    assert service.is_invalid_anonym_viewer_request(question_id=None) is True


def test_is_invalid_anonym_viewer_request_when_param_empty():
    service = WebService(repository=StubWebRepository())

    assert service.is_invalid_anonym_viewer_request(question_id="") is True


def test_is_invalid_anonym_viewer_request_when_param_not_numeric():
    service = WebService(repository=StubWebRepository())

    assert service.is_invalid_anonym_viewer_request(question_id="abc") is True


def test_is_invalid_anonym_viewer_request_when_order_not_found():
    repo = StubWebRepository(order_exists_result=False)
    service = WebService(repository=repo)

    assert service.is_invalid_anonym_viewer_request(question_id="42") is True
    assert repo.last_order_id == 42


def test_is_invalid_anonym_viewer_request_when_order_found_but_not_anonym():
    repo = StubWebRepository(order_exists_result=True, anonym_order_exists_result=False)
    service = WebService(repository=repo)

    assert service.is_invalid_anonym_viewer_request(question_id="42") is True
    assert repo.last_order_id == 42


def test_is_invalid_anonym_viewer_request_when_order_found_and_anonym():
    repo = StubWebRepository(order_exists_result=True, anonym_order_exists_result=True)
    service = WebService(repository=repo)

    assert service.is_invalid_anonym_viewer_request(question_id="42") is False
    assert repo.last_order_id == 42
