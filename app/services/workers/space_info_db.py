from __future__ import annotations

import logging
from typing import Dict, List

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.core.constants import NULLSPACE
from app.db.models import (
    Spaces,
    BotSpaces,
    OrderSpace,
    UnionRole,
    SpaceUnionRoleActive,
    SpaceUnionRole,
)

NULL_SPACE_KEY = NULLSPACE["spacekey"]
NULL_SPACE_TITLE = NULLSPACE["title"]


def safe_commit(session: Session, logger: logging.Logger, log_prefix: str) -> None:
    try:
        session.commit()
    except Exception as exc:
        session.rollback()
        logger.error(log_prefix + f"DB commit failed: {exc}")
        raise


def ensure_null_space(session: Session, logger: logging.Logger, log_prefix: str) -> Spaces:
    null_space = session.query(Spaces).filter_by(spacekey=NULL_SPACE_KEY).first()
    if null_space is None:
        null_space = Spaces(spacekey=NULL_SPACE_KEY, title=NULL_SPACE_TITLE)
        session.add(null_space)
        safe_commit(session, logger, log_prefix)
        logger.info(log_prefix + f"Создан nullspace: id={null_space.id} key={NULL_SPACE_KEY} title={NULL_SPACE_TITLE}")
    else:
        if null_space.title != NULL_SPACE_TITLE:
            old_title = null_space.title
            null_space.title = NULL_SPACE_TITLE
            safe_commit(session, logger, log_prefix)
            logger.info(
                log_prefix
                + f"Title nullspace обновлен: id={null_space.id} key={null_space.spacekey} old_title={old_title} new_title={NULL_SPACE_TITLE}"
            )
    return null_space


def sync_spaces(
    session: Session, spaces_dict: Dict[str, str], null_space: Spaces, logger: logging.Logger, log_prefix: str
) -> None:
    existing: List[Spaces] = session.query(Spaces).all()
    to_delete = [s for s in existing if s.spacekey not in spaces_dict and s.spacekey != NULL_SPACE_KEY]
    for ex in to_delete:
        orders = session.query(OrderSpace).filter(OrderSpace.spaceid == ex.id).all()
        for order_link in orders:
            logger.info(
                log_prefix
                + f"Переведен заказ в nullspace: orderid={order_link.id} old_spaceid={ex.id} -> new_spaceid={null_space.id}"
            )
            order_link.spaceid = null_space.id
        logger.info(log_prefix + f"Удалено пространство: id={ex.id} spacekey={ex.spacekey} title={ex.title}")
        session.delete(ex)
    safe_commit(session, logger, log_prefix)
    for key, title in spaces_dict.items():
        space = session.query(Spaces).filter_by(spacekey=key).first()
        if space is None:
            new_space = Spaces(spacekey=key, title=title)
            session.add(new_space)
            safe_commit(session, logger, log_prefix)
            logger.info(log_prefix + f"Добавлено пространство: id={new_space.id} spacekey={key} title={title}")
        elif space.title != title:
            old_title = space.title
            space.title = title
            safe_commit(session, logger, log_prefix)
            logger.info(
                log_prefix + f"Обновлено пространство: id={space.id} spacekey={key} old_title={old_title} new_title={title}"
            )


def sync_bot_spaces(session: Session, bot_spaces_dict: Dict[str, str], logger: logging.Logger, log_prefix: str) -> None:
    existing: List[BotSpaces] = session.query(BotSpaces).all()
    for ex in existing:
        if ex.spacekey not in bot_spaces_dict:
            logger.info(log_prefix + f"Удалено BotSpace: id={ex.id} spacekey={ex.spacekey} title={ex.title}")
            session.delete(ex)
    safe_commit(session, logger, log_prefix)
    for key, title in bot_spaces_dict.items():
        bspace = session.query(BotSpaces).filter_by(spacekey=key).first()
        if bspace is None:
            new_bspace = BotSpaces(spacekey=key, title=title)
            session.add(new_bspace)
            safe_commit(session, logger, log_prefix)
            logger.info(log_prefix + f"Добавлен BotSpace: id={new_bspace.id} spacekey={key} title={title}")
        elif bspace.title != title:
            old_title = bspace.title
            bspace.title = title
            safe_commit(session, logger, log_prefix)
            logger.info(
                log_prefix + f"Обновлен BotSpace: id={bspace.id} spacekey={key} old_title={old_title} new_title={title}"
            )


def sync_active_flags(session: Session, active_space_keys: List[str], logger: logging.Logger, log_prefix: str) -> None:
    active_space_ids: List[int] = []
    for sk in active_space_keys:
        space = session.query(Spaces).filter_by(spacekey=sk).first()
        if space:
            active_space_ids.append(space.id)
    existing_active = session.query(SpaceUnionRoleActive).all()
    existing_active_ids = {a.spaceid for a in existing_active}
    for sid in active_space_ids:
        rec = session.query(SpaceUnionRoleActive).filter_by(spaceid=sid).first()
        if rec is None:
            new_active = SpaceUnionRoleActive(spaceid=sid, active=1)
            session.add(new_active)
            safe_commit(session, logger, log_prefix)
            logger.info(log_prefix + f"Добавлен активный SpaceUnionRoleActive: id={new_active.id} spaceid={sid} active=1")
        elif rec.active != 1:
            old_value = rec.active
            rec.active = 1
            safe_commit(session, logger, log_prefix)
            logger.info(
                log_prefix + f"Обновлен флаг активности: id={rec.id} spaceid={sid} old_active={old_value} new_active=1"
            )
    for sid in existing_active_ids:
        if sid not in active_space_ids:
            rec = session.query(SpaceUnionRoleActive).filter_by(spaceid=sid).first()
            if rec and rec.active != 0:
                old_value = rec.active
                rec.active = 0
                safe_commit(session, logger, log_prefix)
                logger.info(
                    log_prefix
                    + f"Обновлен флаг активности: id={rec.id} spaceid={sid} old_active={old_value} new_active=0"
                )


def ensure_other_custom_role(session: Session, logger: logging.Logger, log_prefix: str) -> UnionRole:
    other = session.query(UnionRole).filter(and_(UnionRole.name == "Другое", UnionRole.emiasid == 0)).first()
    if other is None:
        other = UnionRole(name="Другое", emiasid=0)
        session.add(other)
        safe_commit(session, logger, log_prefix)
        logger.info(log_prefix + f"Добавлена роль 'Другое': id={other.id} name=Другое emiasid=0")
    return other


def sync_unionroles_supp(
    session: Session,
    unionroles_supp: Dict[str, List[int]],
    supproles_dict: Dict[int, str],
    logger: logging.Logger,
    log_prefix: str,
) -> None:
    for spacekey, ids in unionroles_supp.items():
        space = session.query(Spaces).filter_by(spacekey=spacekey).first()
        if space is None:
            continue
        current_emias_ids: List[int] = []
        for link in session.query(SpaceUnionRole).filter_by(spaceid=space.id).all():
            role = session.query(UnionRole).filter_by(id=link.unionroleid).first()
            if role and role.emiasid != 0:
                current_emias_ids.append(role.emiasid)
        desired_ids = list(dict.fromkeys(ids).keys())
        for emias_id in current_emias_ids:
            if emias_id not in desired_ids:
                role = session.query(UnionRole).filter_by(emiasid=emias_id).first()
                if role:
                    link = session.query(SpaceUnionRole).filter(
                        and_(SpaceUnionRole.spaceid == space.id, SpaceUnionRole.unionroleid == role.id)
                    ).first()
                    if link:
                        logger.info(
                            log_prefix
                            + f"Удалена связь SpaceUnionRole: id={link.id} spaceid={space.id} roleid={role.id} emiasid={emias_id}"
                        )
                        session.delete(link)
        for emias_id in desired_ids:
            role = session.query(UnionRole).filter_by(emiasid=emias_id).first()
            role_name = supproles_dict.get(emias_id)
            if role is None:
                if role_name:
                    role = UnionRole(emiasid=emias_id, name=role_name)
                    session.add(role)
                    session.flush()
                    logger.info(log_prefix + f"Добавлена роль SUPP: id={role.id} emiasid={emias_id} name={role_name}")
                else:
                    continue
            elif role_name and role.name != role_name:
                old_name = role.name
                role.name = role_name
                logger.info(
                    log_prefix
                    + f"Имя роли SUPP обновлено: id={role.id} emiasid={emias_id} old_name={old_name} new_name={role_name}"
                )
            link = session.query(SpaceUnionRole).filter(
                and_(SpaceUnionRole.spaceid == space.id, SpaceUnionRole.unionroleid == role.id)
            ).first()
            if link is None:
                new_link = SpaceUnionRole(spaceid=space.id, unionroleid=role.id)
                session.add(new_link)
                session.flush()
                logger.info(
                    log_prefix
                    + f"Добавлена связь SpaceUnionRole: id={new_link.id} spaceid={space.id} roleid={role.id} emiasid={emias_id}"
                )
    safe_commit(session, logger, log_prefix)


def sync_unionroles_custom(
    session: Session, unionroles_custom: Dict[str, List[str]], logger: logging.Logger, log_prefix: str
) -> None:
    for spacekey, names in unionroles_custom.items():
        space = session.query(Spaces).filter_by(spacekey=spacekey).first()
        if space is None:
            continue
        desired_names = list(dict.fromkeys([n.strip() for n in names if n.strip()]))
        current_custom_names: List[str] = []
        for link in session.query(SpaceUnionRole).filter_by(spaceid=space.id).all():
            role = session.query(UnionRole).filter_by(id=link.unionroleid).first()
            if role and role.emiasid == 0:
                current_custom_names.append(role.name)
        for name in current_custom_names:
            if name not in desired_names:
                role = session.query(UnionRole).filter(and_(UnionRole.name == name, UnionRole.emiasid == 0)).first()
                if role:
                    link = session.query(SpaceUnionRole).filter(
                        and_(SpaceUnionRole.spaceid == space.id, SpaceUnionRole.unionroleid == role.id)
                    ).first()
                    if link:
                        logger.info(
                            log_prefix
                            + f"Удалена кастомная связь SpaceUnionRole: id={link.id} spaceid={space.id} roleid={role.id} name={name}"
                        )
                        session.delete(link)
        for name in desired_names:
            role = session.query(UnionRole).filter(and_(UnionRole.name == name, UnionRole.emiasid == 0)).first()
            if role is None:
                role = UnionRole(name=name, emiasid=0)
                session.add(role)
                session.flush()
                logger.info(log_prefix + f"Добавлена кастомная роль: id={role.id} name={name} emiasid=0")
            link = session.query(SpaceUnionRole).filter(
                and_(SpaceUnionRole.spaceid == space.id, SpaceUnionRole.unionroleid == role.id)
            ).first()
            if link is None:
                new_link = SpaceUnionRole(spaceid=space.id, unionroleid=role.id)
                session.add(new_link)
                session.flush()
                logger.info(
                    log_prefix
                    + f"Добавлена кастомная связь SpaceUnionRole: id={new_link.id} spaceid={space.id} roleid={role.id} name={name}"
                )
    safe_commit(session, logger, log_prefix)

