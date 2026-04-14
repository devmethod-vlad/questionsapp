"""Repository helpers for web HTML endpoints."""

from __future__ import annotations

from dataclasses import dataclass

from app.db.models import AnonymOrder, OrderMess, UserTelegramInfo


@dataclass(slots=True)
class SqlAlchemyWebRepository:
    """SQLAlchemy-backed read helpers used by web endpoint services."""

    session: object

    def has_telegram_user(self, *, telegram_id: str) -> bool:
        return self.session.query(UserTelegramInfo).filter_by(tlgmid=telegram_id).first() is not None

    def order_exists(self, *, order_id: int) -> bool:
        return self.session.query(OrderMess).filter_by(id=order_id).first() is not None

    def anonym_order_exists(self, *, order_id: int) -> bool:
        return self.session.query(AnonymOrder).filter_by(orderid=order_id).first() is not None
