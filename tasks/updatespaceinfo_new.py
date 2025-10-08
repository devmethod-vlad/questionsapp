from __future__ import annotations

from typing import Any, Dict, List, Tuple
import logging, sys
import unicodedata as U, re

import requests
import pandas as pd
import cx_Oracle
from bs4 import BeautifulSoup
from flask import current_app as app
from sqlalchemy import and_
from sqlalchemy.orm import Session
from celery import shared_task
from celery.signals import after_setup_logger

from database import db
from questionsapp.models import (
    Spaces,
    BotSpaces,
    OrderSpace,
    UnionRole,
    SpaceUnionRoleActive,
    SpaceUnionRole,
)
from supp_db.queries.suppallroles import supp_all_roles
from supp_db.supp_connection import dsn

# ==========
# Константы
# ==========
NULL_SPACE_KEY = "nullspacekey"
NULL_SPACE_TITLE = "Не распределено"
REQUEST_TIMEOUT = 20
LOG_PREFIX = "[SpaceInfoUpdate] "

F_PUBLISHED = "Опубликовано на Viewport"
F_SPACEKEY = "Ключ в VP"
F_SPACENAME = "Название пространства"
F_USED_BY_MO = "Пространством пользуются МО"
F_ROLE_IDS = "id ролей, для которых предназначено пространство"
F_CUSTOM_ROLE_NAME = "Название функционала, если отсутствует id роли"

# Настройка root logger для вывода в stdout
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Настройка логгера для Celery
@after_setup_logger.connect
def setup_celery_logger(logger, *args, **kwargs):
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s %(name)s: %(message)s')
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def normalize_text(s: str) -> str:
    s = U.normalize('NFKC', s)  # совместимая нормализация (склеит составные и приведёт совместимые формы)
    s = s.replace('\u00A0', ' ').replace('\u202F', ' ').replace('\u2009', ' ')  # NBSP/узкие пробелы -> обычный
    s = ''.join(ch for ch in s if U.category(ch) != 'Cf')  # убрать форматные (в т.ч. zero-width)
    s = re.sub(r'\s+', ' ', s).strip()  # схлопнуть пробелы по краям и внутри
    return s

# =========================
# Утилиты и обертки сессии
# =========================
def safe_commit(session: Session) -> None:
    try:
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(LOG_PREFIX + f"DB commit failed: {e}")
        raise

def get_session() -> Session:
    return db.session

# ======================
# Загрузка внешних данных
# ======================
def get_supp_roles() -> Dict[int, str]:
    try:
        if app.config.get("FLASK_ENV") == "production":
            with cx_Oracle.connect(
                user=app.config["SUPP_DB_USERNAME"],
                password=app.config["SUPP_DB_PASS"],
                dsn=dsn,
                encoding="UTF-8",
                nencoding="UTF-8",
            ) as con:
                df = pd.read_sql(supp_all_roles, con=con)
        else:
            df = pd.read_parquet("/usr/src/data/all_supp_roles.parquet.gzip")
        df = df.drop_duplicates(subset=["USER_ROLE_ID"])
        return {int(r["USER_ROLE_ID"]): str(r["USER_ROLE"]) for _, r in df.iterrows()}
    except Exception as e:
        logger.error(LOG_PREFIX + f"Supp roles loading failed: {e}")
        raise

def fetch_confluence_spaceinfo() -> List[Dict[str, Any]]:
    try:
        url = app.config["CONFLUENCE_SPACEINFO_PAGE"]
        auth = (app.config["CONFL_BOT_NAME"], app.config["CONFL_BOT_PASS"])
        resp = requests.get(url, auth=auth, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        body_html = resp.json()["body"]["storage"]["value"]

        soup = BeautifulSoup(body_html, "lxml")
        table = soup.find("table")
        if table is None:
            raise ValueError("Table not found in Confluence storage body")

        headers = [th.get_text(strip=True) for th in table.find_all("th")]
        rows = []
        for tr in table.find_all("tr"):
            tds = tr.find_all("td")
            if not tds:
                continue
            row = {headers[i]: td.get_text(strip=True) for i, td in enumerate(tds)}
            rows.append(row)
        return rows
    except Exception as e:
        logger.error(LOG_PREFIX + f"Confluence fetch/parse failed: {e}")
        raise

def parse_source_rows(
    rows: List[Dict[str, str]]
) -> Tuple[
    Dict[str, str],  # spaces_dict
    Dict[str, str],  # bot_spaces_dict
    Dict[str, List[int]],  # unionroles_supp
    Dict[str, List[str]],  # unionroles_custom
    List[str],  # active_space_keys
    List[str],  # rows_with_error
]:
    spaces_dict: Dict[str, str] = {}
    bot_spaces_dict: Dict[str, str] = {}
    unionroles_supp: Dict[str, List[int]] = {}
    unionroles_custom: Dict[str, List[str]] = {}
    active_space_keys: List[str] = []
    rows_with_error: List[str] = []

    for item in rows:
        if not item:
            continue

        spacekey = item.get(F_SPACEKEY, "").strip()
        spacename = item.get(F_SPACENAME, "").strip()

        is_published = item.get(F_PUBLISHED, "").strip().lower() == "да"
        used_by_mo = item.get(F_USED_BY_MO, "").strip().lower() == "да"
        role_ids_raw = item.get(F_ROLE_IDS, "").strip()
        custom_names_raw = item.get(F_CUSTOM_ROLE_NAME, "").strip()

        if is_published and spacekey and spacename:
            spaces_dict[spacekey] = spacename
        if used_by_mo and spacekey and spacename:
            bot_spaces_dict[spacekey] = spacename
        if role_ids_raw or custom_names_raw:
            if spacekey:
                active_space_keys.append(spacekey)
        if role_ids_raw and spacekey:
            try:
                ids = []
                for piece in role_ids_raw.split(";"):
                    s = piece.strip()
                    if not s:
                        continue
                    ids.append(int(s))
                if ids:
                    unique_ids = list(dict.fromkeys(ids).keys())
                    unionroles_supp[spacekey] = unique_ids
            except Exception:
                if spacename:
                    rows_with_error.append(spacename)
        if custom_names_raw and spacekey:
            try:
                names: List[str] = []
                for piece in custom_names_raw.split(";"):
                    n = piece.strip()
                    if n and n.lower() != "другое" and n not in names:
                        names.append(n)
                if names:
                    unionroles_custom[spacekey] = names
            except Exception:
                if spacename:
                    rows_with_error.append(spacename)
    return (
        spaces_dict,
        bot_spaces_dict,
        unionroles_supp,
        unionroles_custom,
        active_space_keys,
        rows_with_error,
    )

# ======================
# Операции с БД с логированием
# ======================
def ensure_null_space(session: Session) -> Spaces:
    null_space = session.query(Spaces).filter_by(spacekey=NULL_SPACE_KEY).first()
    if null_space is None:
        null_space = Spaces(spacekey=NULL_SPACE_KEY, title=NULL_SPACE_TITLE)
        session.add(null_space)
        safe_commit(session)
        logger.info(
            LOG_PREFIX
            + f"Создан nullspace: id={null_space.id} key={NULL_SPACE_KEY} title={NULL_SPACE_TITLE}"
        )
    else:
        # Поддерживать title актуальным
        if normalize_text(null_space.title) != normalize_text(NULL_SPACE_TITLE):
            old_title = null_space.title
            null_space.title = NULL_SPACE_TITLE
            safe_commit(session)
            logger.info(
                LOG_PREFIX
                + f"Title nullspace обновлен: id={null_space.id} key={null_space.spacekey} old_title={old_title} new_title={NULL_SPACE_TITLE}"
            )
    return null_space

def sync_spaces(session: Session, spaces_dict: Dict[str, str], null_space: Spaces) -> None:
    existing: List[Spaces] = session.query(Spaces).all()
    to_delete = [s for s in existing if s.spacekey not in spaces_dict and s.spacekey != NULL_SPACE_KEY]
    for ex in to_delete:
        orders = session.query(OrderSpace).filter(OrderSpace.spaceid == ex.id).all()
        for o in orders:
            logger.info(
                LOG_PREFIX +
                f"Переведен заказ в nullspace: orderid={o.id} old_spaceid={ex.id} -> new_spaceid={null_space.id}"
            )
            o.spaceid = null_space.id
        logger.info(
            LOG_PREFIX +
            f"Удалено пространство: id={ex.id} spacekey={ex.spacekey} title={ex.title}"
        )
        session.delete(ex)
    safe_commit(session)
    for key, title in spaces_dict.items():
        space = session.query(Spaces).filter_by(spacekey=key).first()
        if space is None:
            new_space = Spaces(spacekey=key, title=title)
            session.add(new_space)
            safe_commit(session)
            logger.info(
                LOG_PREFIX +
                f"Добавлено пространство: id={new_space.id} spacekey={key} title={title}"
            )
        else:
            if normalize_text(space.title) != normalize_text(title):
                old_title = space.title
                space.title = title
                safe_commit(session)
                logger.info(
                    LOG_PREFIX +
                    f"Обновлено пространство: id={space.id} spacekey={key} old_title={old_title} new_title={title}"
                )

def sync_bot_spaces(session: Session, bot_spaces_dict: Dict[str, str]) -> None:
    existing: List[BotSpaces] = session.query(BotSpaces).all()
    for ex in existing:
        if ex.spacekey not in bot_spaces_dict:
            logger.info(
                LOG_PREFIX +
                f"Удалено BotSpace: id={ex.id} spacekey={ex.spacekey} title={ex.title}"
            )
            session.delete(ex)
    safe_commit(session)
    for key, title in bot_spaces_dict.items():
        bspace = session.query(BotSpaces).filter_by(spacekey=key).first()
        if bspace is None:
            new_bspace = BotSpaces(spacekey=key, title=title)
            session.add(new_bspace)
            safe_commit(session)
            logger.info(
                LOG_PREFIX +
                f"Добавлен BotSpace: id={new_bspace.id} spacekey={key} title={title}"
            )
        else:
            if normalize_text(bspace.title) != normalize_text(title):
                old_title = bspace.title
                bspace.title = title
                safe_commit(session)
                logger.info(
                    LOG_PREFIX +
                    f"Обновлен BotSpace: id={bspace.id} spacekey={key} old_title={old_title} new_title={title}"
                )

def sync_active_flags(session: Session, active_space_keys: List[str]) -> None:
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
            safe_commit(session)
            logger.info(
                LOG_PREFIX +
                f"Добавлен активный SpaceUnionRoleActive: id={new_active.id} spaceid={sid} active=1"
            )
        else:
            if rec.active != 1:
                old_value = rec.active
                rec.active = 1
                safe_commit(session)
                logger.info(
                    LOG_PREFIX +
                    f"Обновлен флаг активности: id={rec.id} spaceid={sid} old_active={old_value} new_active=1"
                )
    for sid in existing_active_ids:
        if sid not in active_space_ids:
            rec = session.query(SpaceUnionRoleActive).filter_by(spaceid=sid).first()
            if rec and rec.active != 0:
                old_value = rec.active
                rec.active = 0
                safe_commit(session)
                logger.info(
                    LOG_PREFIX +
                    f"Обновлен флаг активности: id={rec.id} spaceid={sid} old_active={old_value} new_active=0"
                )

def ensure_other_custom_role(session: Session) -> UnionRole:
    other = session.query(UnionRole).filter(
        and_(UnionRole.name == "Другое", UnionRole.emiasid == 0)
    ).first()
    if other is None:
        other = UnionRole(name="Другое", emiasid=0)
        session.add(other)
        safe_commit(session)
        logger.info(
            LOG_PREFIX +
            f"Добавлена роль 'Другое': id={other.id} name=Другое emiasid=0"
        )
    return other

def sync_unionroles_supp(
    session: Session,
    unionroles_supp: Dict[str, List[int]],
    supproles_dict: Dict[int, str],
) -> None:
    for spacekey, ids in unionroles_supp.items():
        space = session.query(Spaces).filter_by(spacekey=spacekey).first()
        if space is None:
            continue
        current_emias_ids: List[int] = []
        for link in session.query(SpaceUnionRole).filter_by(spaceid=space.id).all():
            ur = session.query(UnionRole).filter_by(id=link.unionroleid).first()
            if ur and ur.emiasid != 0:
                current_emias_ids.append(ur.emiasid)
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
                            LOG_PREFIX +
                            f"Удалена связь SpaceUnionRole: id={link.id} spaceid={space.id} roleid={role.id} emiasid={emias_id}"
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
                    logger.info(
                        LOG_PREFIX +
                        f"Добавлена роль SUPP: id={role.id} emiasid={emias_id} name={role_name}"
                    )
                else:
                    continue
            else:
                if role_name and normalize_text(role.name) != normalize_text(role_name):
                    old_name = role.name
                    role.name = role_name
                    logger.info(
                        LOG_PREFIX +
                        f"Имя роли SUPP обновлено: id={role.id} emiasid={emias_id} old_name={old_name} new_name={role_name}"
                    )
            link = session.query(SpaceUnionRole).filter(
                and_(SpaceUnionRole.spaceid == space.id, SpaceUnionRole.unionroleid == role.id)
            ).first()
            if link is None:
                new_link = SpaceUnionRole(spaceid=space.id, unionroleid=role.id)
                session.add(new_link)
                session.flush()
                logger.info(
                    LOG_PREFIX +
                    f"Добавлена связь SpaceUnionRole: id={new_link.id} spaceid={space.id} roleid={role.id} emiasid={emias_id}"
                )
    safe_commit(session)

def sync_unionroles_custom(
    session: Session,
    unionroles_custom: Dict[str, List[str]],
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
                role = session.query(UnionRole).filter(
                    and_(UnionRole.name == name, UnionRole.emiasid == 0)
                ).first()
                if role:
                    link = session.query(SpaceUnionRole).filter(
                        and_(SpaceUnionRole.spaceid == space.id, SpaceUnionRole.unionroleid == role.id)
                    ).first()
                    if link:
                        logger.info(
                            LOG_PREFIX +
                            f"Удалена кастомная связь SpaceUnionRole: id={link.id} spaceid={space.id} roleid={role.id} name={name}"
                        )
                        session.delete(link)
        for name in desired_names:
            role = session.query(UnionRole).filter(
                and_(UnionRole.name == name, UnionRole.emiasid == 0)
            ).first()
            if role is None:
                role = UnionRole(name=name, emiasid=0)
                session.add(role)
                session.flush()
                logger.info(
                    LOG_PREFIX +
                    f"Добавлена кастомная роль: id={role.id} name={name} emiasid=0"
                )
            link = session.query(SpaceUnionRole).filter(
                and_(SpaceUnionRole.spaceid == space.id, SpaceUnionRole.unionroleid == role.id)
            ).first()
            if link is None:
                new_link = SpaceUnionRole(spaceid=space.id, unionroleid=role.id)
                session.add(new_link)
                session.flush()
                logger.info(
                    LOG_PREFIX +
                    f"Добавлена кастомная связь SpaceUnionRole: id={new_link.id} spaceid={space.id} roleid={role.id} name={name}"
                )
    safe_commit(session)

@shared_task(
    bind=True,
    autoretry_for=(requests.RequestException, cx_Oracle.Error),
    retry_backoff=True,
    max_retries=3,
    acks_late=False,
)
def update_spaces_info_ref(self) -> Dict[str, Any]:
    session = get_session()
    try:
        supproles_dict = get_supp_roles()
        source_rows = fetch_confluence_spaceinfo()
        (
            spaces_dict,
            bot_spaces_dict,
            unionroles_supp,
            unionroles_custom,
            active_space_keys,
            rows_with_error,
        ) = parse_source_rows(source_rows)
        if rows_with_error and app.config.get("FLASK_ENV") == "development":
            logger.warning(
                LOG_PREFIX + "Ошибки при обработке строк таблицы пространств: "
                + ", ".join(rows_with_error)
            )
        null_space = ensure_null_space(session)
        sync_spaces(session, spaces_dict, null_space)
        sync_bot_spaces(session, bot_spaces_dict)
        sync_active_flags(session, active_space_keys)
        sync_unionroles_supp(session, unionroles_supp, supproles_dict)
        ensure_other_custom_role(session)
        sync_unionroles_custom(session, unionroles_custom)

        logger.info(LOG_PREFIX + "Update finished successfully")
        return {"status": "ok"}
    except Exception as e:
        logger.error(LOG_PREFIX + f"Global error: {e}")
        return {"status": "error", "error_mess": f"Ошибка обновления: {e}"}
