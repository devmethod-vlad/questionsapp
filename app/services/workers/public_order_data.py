from __future__ import annotations

from typing import Any

from sqlalchemy import and_, desc

from app.db.engine import SessionFactory
from app.db.models import (
    AnswerAttachment,
    AnswerMess,
    AppConfig,
    Attachment,
    OrderAttachment,
    OrderMess,
    OrderPublic,
    OrderSpace,
    OrderStatus,
    OrderUnionRole,
    Spaces,
    UnionRole,
)


def set_public_active(value: int) -> None:
    app_conf = SessionFactory().query(AppConfig).order_by(desc("created_at")).limit(1).first()
    app_conf.ispublicactive = value
    SessionFactory().commit()


def get_order_space(order_id: int) -> OrderSpace | None:
    return SessionFactory().query(OrderSpace).filter_by(orderid=order_id).first()


def list_space_orders(space_id: int) -> list[OrderSpace]:
    return SessionFactory().query(OrderSpace).filter(OrderSpace.spaceid == space_id).all()


def get_other_union_role() -> UnionRole:
    return SessionFactory().query(UnionRole).filter(
        and_((UnionRole.name == "Другое"), (UnionRole.emiasid == 0))
    ).first()


def get_order_public(order_id: int) -> OrderPublic | None:
    return SessionFactory().query(OrderPublic).filter_by(orderid=order_id).first()


def get_order_status(order_id: int) -> OrderStatus | None:
    return SessionFactory().query(OrderStatus).filter_by(orderid=order_id).first()


def get_order_union_role(order_id: int) -> OrderUnionRole | None:
    return SessionFactory().query(OrderUnionRole).filter_by(orderid=order_id).first()


def get_answer_by_order(order_id: int) -> AnswerMess | None:
    return SessionFactory().query(AnswerMess).filter_by(orderid=order_id).first()


def get_space_by_id(space_id: int) -> Spaces | None:
    return SessionFactory().query(Spaces).filter_by(id=space_id).first()


def get_order_with_answer(order_id: int) -> tuple[OrderMess | None, AnswerMess | None]:
    order = SessionFactory().query(OrderMess).filter_by(id=order_id).first()
    answer = SessionFactory().query(AnswerMess).filter_by(orderid=order_id).first()
    return order, answer


def list_public_order_attachment_paths(order_id: int) -> list[str]:
    paths: list[str] = []
    attachs = (
        SessionFactory().query(OrderAttachment).filter_by(orderid=order_id).order_by(desc(OrderAttachment.created_at)).all()
    )
    for attach_item in attachs:
        attachment = SessionFactory().query(Attachment).filter_by(id=attach_item.attachid).first()
        if attachment and attachment.public == 1:
            paths.append(attachment.path)
    return paths


def list_public_answer_attachment_paths(answer_id: int) -> list[str]:
    paths: list[str] = []
    answer_attachments = (
        SessionFactory()
        .query(AnswerAttachment)
        .filter_by(answerid=answer_id)
        .order_by(desc(AnswerAttachment.created_at))
        .all()
    )
    for answer_attachment in answer_attachments:
        attachment = SessionFactory().query(Attachment).filter_by(id=answer_attachment.attachid).first()
        if attachment and attachment.public == 1:
            paths.append(attachment.path)
    return paths


def get_union_role_name(order_id: int, other_role_id: int) -> str:
    order_union_role = SessionFactory().query(OrderUnionRole).filter_by(orderid=order_id).first()
    if order_union_role is None:
        return ""
    if order_union_role.unionroleid == other_role_id:
        return ""

    union_role = SessionFactory().query(UnionRole).filter_by(id=order_union_role.unionroleid).first()
    if union_role is None:
        return ""
    return union_role.name


def list_space_public_order_ids_with_answer_date(space_id: int, other_union_role_id: int) -> tuple[list[dict[str, Any]], bool]:
    space_orders_list: list[dict[str, Any]] = []
    role_out_flag = False
    all_space_orders = list_space_orders(space_id)

    for space_order in all_space_orders:
        public_order = get_order_public(space_order.orderid)
        order_status = get_order_status(space_order.orderid)
        order_union_role = get_order_union_role(space_order.orderid)

        if order_union_role is not None and public_order is not None:
            if order_union_role.unionroleid != other_union_role_id:
                role_out_flag = True

        if order_status and order_status.statusid not in [1, 2, 5] and public_order:
            answer = get_answer_by_order(int(space_order.orderid))
            if answer is not None:
                space_orders_list.append({"id": space_order.orderid, "answer_date": answer.modified_at})

    space_orders_list.sort(key=lambda item: item["answer_date"], reverse=True)
    return space_orders_list, role_out_flag


def delete_order_public(order_id: int) -> None:
    check_public = SessionFactory().query(OrderPublic).filter_by(orderid=order_id).first()
    if check_public is not None:
        SessionFactory().delete(check_public)
        SessionFactory().commit()

