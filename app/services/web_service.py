"""Application service for web HTML endpoint orchestration."""

from __future__ import annotations

from dataclasses import dataclass

from app.repositories.web_repository import SqlAlchemyWebRepository


@dataclass(slots=True)
class WebService:
    """Business logic for web/html routes."""

    repository: SqlAlchemyWebRepository

    def is_authorized_telegram_user(self, *, telegram_id: str | None) -> tuple[bool, bool]:
        """Return tuple of (no_params, is_auth) for webappauth endpoint."""

        no_params = not bool(telegram_id)
        if no_params:
            return True, False

        return False, self.repository.has_telegram_user(telegram_id=str(telegram_id))

    def is_invalid_anonym_viewer_request(self, *, question_id: str | None) -> bool:
        """Return whether anonym viewer request should be treated as invalid."""

        if not question_id:
            return True

        order_id = int(question_id)
        if not self.repository.order_exists(order_id=order_id):
            return True

        return not self.repository.anonym_order_exists(order_id=order_id)
