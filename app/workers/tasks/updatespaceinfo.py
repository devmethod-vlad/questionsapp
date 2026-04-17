from __future__ import annotations

from typing import Any, Dict, List, Tuple
import logging, sys

import requests
import pandas as pd
import cx_Oracle
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from celery import shared_task
from celery.signals import after_setup_logger

from app.core.settings import get_settings
from app.integrations import ConfluenceGateway
from app.db.engine import SessionFactory
from app.services.workers.space_info_db import (
    ensure_null_space,
    ensure_other_custom_role,
    sync_active_flags,
    sync_bot_spaces,
    sync_spaces,
    sync_unionroles_custom,
    sync_unionroles_supp,
)
from app.repositories.supp_db.queries.suppallroles import supp_all_roles
from app.integrations.oracle.supp_connection import dsn


SETTINGS = get_settings()
LOG_PREFIX = "[SpaceInfoUpdate] "

F_PUBLISHED = "Опубликовано на Viewport"
F_SPACEKEY = "Ключ в VP"
F_SPACENAME = "Название пространства"
F_USED_BY_MO = "Пространством пользуются МО"
F_ROLE_IDS = "id ролей, для которых предназначено пространство"
F_CUSTOM_ROLE_NAME = "Название функционала, если отсутствует id роли"

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@after_setup_logger.connect
def setup_celery_logger(logger, *args, **kwargs):
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s %(name)s: %(message)s')
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def get_session() -> Session:
    return SessionFactory()


def get_supp_roles() -> Dict[int, str]:
    try:
        if SETTINGS.prod:
            with cx_Oracle.connect(
                user=SETTINGS.etd2_db_username,
                password=SETTINGS.etd2_db_pass,
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
        url = SETTINGS.confluence_spaceinfo_page
        payload = ConfluenceGateway(
            base_url=SETTINGS.confluence_url,
            bearer_token=SETTINGS.iac_bot_token,
        ).get_storage_page(url=url)
        body_html = payload["body"]["storage"]["value"]

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
    Dict[str, str],
    Dict[str, str],
    Dict[str, List[int]],
    Dict[str, List[str]],
    List[str],
    List[str],
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
        if (role_ids_raw or custom_names_raw) and spacekey:
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
                    unionroles_supp[spacekey] = list(dict.fromkeys(ids).keys())
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


@shared_task(
    bind=True,
    autoretry_for=(requests.RequestException, cx_Oracle.Error),
    retry_backoff=True,
    max_retries=3,
    acks_late=False,
)
def update_spaces_info(self) -> Dict[str, Any]:
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
        if rows_with_error and not SETTINGS.prod:
            logger.warning(
                LOG_PREFIX + "Ошибки при обработке строк таблицы пространств: "
                + ", ".join(rows_with_error)
            )
        null_space = ensure_null_space(session, logger, LOG_PREFIX)
        sync_spaces(session, spaces_dict, null_space, logger, LOG_PREFIX)
        sync_bot_spaces(session, bot_spaces_dict, logger, LOG_PREFIX)
        sync_active_flags(session, active_space_keys, logger, LOG_PREFIX)
        sync_unionroles_supp(session, unionroles_supp, supproles_dict, logger, LOG_PREFIX)
        ensure_other_custom_role(session, logger, LOG_PREFIX)
        sync_unionroles_custom(session, unionroles_custom, logger, LOG_PREFIX)

        logger.info(LOG_PREFIX + "Update finished successfully")
        return {"status": "ok"}
    except Exception as e:
        logger.error(LOG_PREFIX + f"Global error: {e}")
        return {"status": "error", "error_mess": f"Ошибка обновления: {e}"}
