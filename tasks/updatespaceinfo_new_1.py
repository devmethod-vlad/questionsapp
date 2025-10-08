from __future__ import annotations

from typing import Any, Dict, List, Tuple
import logging

import requests
import pandas as pd
import cx_Oracle
from bs4 import BeautifulSoup
from flask import current_app as app
from sqlalchemy import and_
from sqlalchemy.orm import Session
from celery import shared_task

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

# Поля таблицы на портале (Confluence)
F_PUBLISHED = "Опубликовано на Viewport"
F_SPACEKEY = "Ключ в VP"
F_SPACENAME = "Название пространства"
F_USED_BY_MO = "Пространством пользуются МО"
F_ROLE_IDS = "id ролей, для которых предназначено пространство"
F_CUSTOM_ROLE_NAME = "Название функционала, если отсутствует id роли"

logger = logging.getLogger(__name__)


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
    """
    Возвращает словарь {USER_ROLE_ID: USER_ROLE} из Oracle в prod или из parquet в dev.
    """
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
    """
    Получает JSON Confluence, извлекает HTML тела страницы и парсит таблицу в список dict-строк.
    """
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


# ======================
# Преобразование данных
# ======================
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

        # Флаг публикации
        is_published = item.get(F_PUBLISHED, "").strip().lower() == "да"
        # Флаг для МО
        used_by_mo = item.get(F_USED_BY_MO, "").strip().lower() == "да"

        # ID ролей и кастомные названия
        role_ids_raw = item.get(F_ROLE_IDS, "").strip()
        custom_names_raw = item.get(F_CUSTOM_ROLE_NAME, "").strip()

        # 1) Словарь Spaces (только опубликованные, с корректными полями)
        if is_published and spacekey and spacename:
            spaces_dict[spacekey] = spacename

        # 2) Словарь BotSpaces (только используемые МО, с корректными полями)
        if used_by_mo and spacekey and spacename:
            bot_spaces_dict[spacekey] = spacename

        # 3) Активность объединенных ролей
        if role_ids_raw or custom_names_raw:
            if spacekey:
                active_space_keys.append(spacekey)

        # 4) Парсинг unionroles_supp
        if role_ids_raw and spacekey:
            try:
                ids = []
                for piece in role_ids_raw.split(";"):
                    s = piece.strip()
                    if not s:
                        continue
                    # В исходном коде был int(...) без строгой проверки, оставим эквивалентно
                    ids.append(int(s))
                if ids:
                    # Убрать дубликаты, сохранив порядок
                    unique_ids = list(dict.fromkeys(ids).keys())
                    unionroles_supp[spacekey] = unique_ids
            except Exception:
                # Сохраняем имя пространства для отладки
                if spacename:
                    rows_with_error.append(spacename)

        # 5) Парсинг unionroles_custom
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
# Операции с БД
# ======================
def ensure_null_space(session: Session) -> Spaces:
    """
    Гарантирует наличие пространства-перехватчика.
    """
    null_space = session.query(Spaces).filter_by(spacekey=NULL_SPACE_KEY).first()
    if null_space is None:
        null_space = Spaces(spacekey=NULL_SPACE_KEY, title=NULL_SPACE_TITLE)
        session.add(null_space)
        safe_commit(session)
    else:
        # Поддерживать title актуальным
        if null_space.title != NULL_SPACE_TITLE:
            null_space.title = NULL_SPACE_TITLE
            safe_commit(session)
    return null_space


def sync_spaces(session: Session, spaces_dict: Dict[str, str], null_space: Spaces) -> None:
    """
    Синхронизирует таблицу Spaces с источником:
    - Удаляет отсутствующие, предварительно переводя их заказы в nullspace.
    - Добавляет недостающие.
    - Обновляет title при изменении.
    """
    existing: List[Spaces] = session.query(Spaces).all()

    # Удаление отсутствующих (кроме nullspace)
    to_delete = [s for s in existing if s.spacekey not in spaces_dict and s.spacekey != NULL_SPACE_KEY]
    for ex in to_delete:
        orders = session.query(OrderSpace).filter(OrderSpace.spaceid == ex.id).all()
        for o in orders:
            o.spaceid = null_space.id
        session.delete(ex)
    safe_commit(session)

    # Добавление и обновление
    for key, title in spaces_dict.items():
        space = session.query(Spaces).filter_by(spacekey=key).first()
        if space is None:
            session.add(Spaces(spacekey=key, title=title))
        else:
            if space.title != title:
                space.title = title
    safe_commit(session)


def sync_bot_spaces(session: Session, bot_spaces_dict: Dict[str, str]) -> None:
    """
    Синхронизирует таблицу BotSpaces с источником:
    - Удаляет отсутствующие.
    - Добавляет недостающие.
    - Обновляет title при изменении.
    """
    existing: List[BotSpaces] = session.query(BotSpaces).all()
    for ex in existing:
        if ex.spacekey not in bot_spaces_dict:
            session.delete(ex)
    safe_commit(session)

    for key, title in bot_spaces_dict.items():
        bspace = session.query(BotSpaces).filter_by(spacekey=key).first()
        if bspace is None:
            session.add(BotSpaces(spacekey=key, title=title))
        else:
            if bspace.title != title:
                bspace.title = title
    safe_commit(session)


def sync_active_flags(session: Session, active_space_keys: List[str]) -> None:
    """
    Обновляет SpaceUnionRoleActive:
    - Для новых активных пространств (по ключам) ставит active=1 (создаёт запись при необходимости).
    - Для тех, кто перестал быть активным — active=0.
    """
    # Собираем id пространств для ключей
    active_space_ids: List[int] = []
    for sk in active_space_keys:
        space = session.query(Spaces).filter_by(spacekey=sk).first()
        if space:
            active_space_ids.append(space.id)

    # Сейчас активные в БД
    existing_active = session.query(SpaceUnionRoleActive).all()
    existing_active_ids = {a.spaceid for a in existing_active}

    # Включить активность
    for sid in active_space_ids:
        rec = session.query(SpaceUnionRoleActive).filter_by(spaceid=sid).first()
        if rec is None:
            session.add(SpaceUnionRoleActive(spaceid=sid, active=1))
        else:
            if rec.active != 1:
                rec.active = 1

    # Отключить активность у тех, кого нет среди новых
    for sid in existing_active_ids:
        if sid not in active_space_ids:
            rec = session.query(SpaceUnionRoleActive).filter_by(spaceid=sid).first()
            if rec and rec.active != 0:
                rec.active = 0

    safe_commit(session)


def ensure_other_custom_role(session: Session) -> UnionRole:
    """
    Обеспечивает наличие объединенной роли 'Другое' (emiasid=0).
    """
    other = session.query(UnionRole).filter(
        and_(UnionRole.name == "Другое", UnionRole.emiasid == 0)
    ).first()
    if other is None:
        other = UnionRole(name="Другое", emiasid=0)
        session.add(other)
        safe_commit(session)
    return other


def sync_unionroles_supp(
    session: Session,
    unionroles_supp: Dict[str, List[int]],
    supproles_dict: Dict[int, str],
) -> None:
    """
    Синхронизирует связки объединенных ролей с пространствами для SUPP-id ролей (emiasid != 0).
    - Создает/обновляет UnionRole по emiasid и имени из supproles_dict.
    - Удаляет лишние SpaceUnionRole, которых нет в новом списке.
    - Создает отсутствующие SpaceUnionRole.
    """
    for spacekey, ids in unionroles_supp.items():
        space = session.query(Spaces).filter_by(spacekey=spacekey).first()
        if space is None:
            continue

        # Текущие emiasid, привязанные к пространству
        current_emias_ids: List[int] = []
        for link in session.query(SpaceUnionRole).filter_by(spaceid=space.id).all():
            ur = session.query(UnionRole).filter_by(id=link.unionroleid).first()
            if ur and ur.emiasid != 0:
                current_emias_ids.append(ur.emiasid)

        desired_ids = list(dict.fromkeys(ids).keys())

        # Удаление лишних связей
        for emias_id in current_emias_ids:
            if emias_id not in desired_ids:
                role = session.query(UnionRole).filter_by(emiasid=emias_id).first()
                if role:
                    link = session.query(SpaceUnionRole).filter(
                        and_(SpaceUnionRole.spaceid == space.id, SpaceUnionRole.unionroleid == role.id)
                    ).first()
                    if link:
                        session.delete(link)

        # Создание отсутствующих ролей и связей
        for emias_id in desired_ids:
            # Роль
            role = session.query(UnionRole).filter_by(emiasid=emias_id).first()
            role_name = supproles_dict.get(emias_id)
            if role is None:
                if role_name:
                    role = UnionRole(emiasid=emias_id, name=role_name)
                    session.add(role)
                    session.flush()  # получить role.id
                else:
                    # Если нет имени в словаре — пропускаем, как и в исходнике (silent pass)
                    continue
            else:
                # Актуализируем имя роли, если изменилось
                if role_name and role.name != role_name:
                    role.name = role_name

            # Связь
            link = session.query(SpaceUnionRole).filter(
                and_(SpaceUnionRole.spaceid == space.id, SpaceUnionRole.unionroleid == role.id)
            ).first()
            if link is None:
                session.add(SpaceUnionRole(spaceid=space.id, unionroleid=role.id))

    safe_commit(session)


def sync_unionroles_custom(
    session: Session,
    unionroles_custom: Dict[str, List[str]],
) -> None:
    """
    Синхронизирует кастомные объединенные роли (emiasid == 0):
    - Удаляет кастомные связи, которых нет в списке.
    - Создает недостающие роли и связи.
    """
    for spacekey, names in unionroles_custom.items():
        space = session.query(Spaces).filter_by(spacekey=spacekey).first()
        if space is None:
            continue

        desired_names = list(dict.fromkeys([n.strip() for n in names if n.strip()]))
        # Текущие кастомные имена, привязанные к пространству
        current_custom_names: List[str] = []
        for link in session.query(SpaceUnionRole).filter_by(spaceid=space.id).all():
            role = session.query(UnionRole).filter_by(id=link.unionroleid).first()
            if role and role.emiasid == 0:
                current_custom_names.append(role.name)

        # Удаление лишних
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
                        session.delete(link)

        # Добавление недостающих
        for name in desired_names:
            role = session.query(UnionRole).filter(
                and_(UnionRole.name == name, UnionRole.emiasid == 0)
            ).first()
            if role is None:
                role = UnionRole(name=name, emiasid=0)
                session.add(role)
                session.flush()

            link = session.query(SpaceUnionRole).filter(
                and_(SpaceUnionRole.spaceid == space.id, SpaceUnionRole.unionroleid == role.id)
            ).first()
            if link is None:
                session.add(SpaceUnionRole(spaceid=space.id, unionroleid=role.id))

    safe_commit(session)


# ======================
# Celery Task
# ======================
@shared_task(
    bind=True,
    autoretry_for=(requests.RequestException, cx_Oracle.Error),
    retry_backoff=True,
    max_retries=3,
    acks_late=False,  # включать только при чётком понимании семантики
)
def update_spaces_info_ref(self) -> Dict[str, Any]:
    """
    Основная задача: подтянуть данные, распарсить, синхронизировать все сущности.
    Возвращает {"status": "ok"} либо {"status": "error", "error_mess": "..."}.
    """
    session = get_session()

    try:
        # 1) Внешние источники
        supproles_dict = get_supp_roles()
        source_rows = fetch_confluence_spaceinfo()

        # 2) Парсинг и подготовка словарей
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

        # 3) Гарантируем наличие nullspace
        null_space = ensure_null_space(session)

        # 4) Синхронизация Spaces
        sync_spaces(session, spaces_dict, null_space)

        # 5) Синхронизация BotSpaces
        sync_bot_spaces(session, bot_spaces_dict)

        # 6) Синхронизация флагов активности объединенных ролей
        sync_active_flags(session, active_space_keys)

        # 7) Синхронизация системных объединенных ролей (по SUPP id)
        sync_unionroles_supp(session, unionroles_supp, supproles_dict)

        # 8) Обеспечиваем наличие роли "Другое"
        ensure_other_custom_role(session)

        # 9) Синхронизация кастомных объединенных ролей (emiasid==0)
        sync_unionroles_custom(session, unionroles_custom)

        logger.info(LOG_PREFIX + "Update finished successfully")
        return {"status": "ok"}
    except Exception as e:
        logger.error(LOG_PREFIX + f"Global error: {e}")
        return {"status": "error", "error_mess": f"Ошибка обновления: {e}"}
