"""Legacy-compatible admin helpers without Flask runtime dependencies.

This module preserves historic payload envelopes for admin/service endpoints
while using FastAPI-native runtime configuration and SQLAlchemy sessions.
"""

from __future__ import annotations

import datetime
import os
from io import BytesIO
from typing import Any

import pandas as pd
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from pytz import timezone

from app.core.runtime_config import get_config_value
from app.services.common.telegram import tg_post
from questionsapp.models import (
    AnswerAttachment,
    AnswerTelegramAttachment,
    Attachment,
    OrderAttachment,
    OrderTelegramAttachment,
    SyncAttachments,
    TelegramAttachment,
    TelPhrazeStats,
    UserTelegramInfo,
)


EAST_TZ = timezone("Europe/Moscow")
EXCEL_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _excel_response(dataframe: pd.DataFrame, filename: str) -> StreamingResponse:
    """Convert a DataFrame to XLSX and return a FastAPI streaming response."""

    workbook = Workbook()
    worksheet = workbook.active
    for row in dataframe_to_rows(dataframe, index=False, header=True):
        worksheet.append(row)

    output = BytesIO()
    workbook.save(output)
    workbook.close()
    output.seek(0)
    return StreamingResponse(
        output,
        media_type=EXCEL_MIME,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


class AdminLegacyCompatService:
    """Native implementation of legacy admin/statistics utility scenarios."""

    @staticmethod
    def execute_service_action(payload: dict[str, Any], *, session) -> dict[str, Any] | None:
        """Handle legacy `/service/` actions that were previously delegated to bridge."""

        action = payload.get("action")
        if action == "changefilepublicity":
            return AdminLegacyCompatService._change_attachment_publicity(
                session=session,
                attachid=payload.get("attachid"),
                publicflag=payload.get("publicflag"),
            )
        if action == "deleteattachment":
            return AdminLegacyCompatService._delete_attachment(
                session=session,
                attach_target=payload.get("attach_target"),
                attachid=payload.get("attachid"),
                orderid=payload.get("orderid"),
                userid=payload.get("userid"),
            )
        if action == "updtspacesbyconfl":
            from app.workers.tasks.updatespaceinfo import update_spaces_info

            update_spaces_info.delay()
            return {"status": "ok"}

        return None

    @staticmethod
    def _change_attachment_publicity(*, session, attachid: Any, publicflag: Any) -> dict[str, Any]:
        if not attachid:
            return {"status": "error", "error_mess": "WARN: No attachid"}

        attachment = session.query(Attachment).filter_by(id=int(attachid)).first()
        if attachment is None:
            return {"status": "error", "error_mess": "WARN: No attachment with attachid"}

        attachment.public = int(publicflag)
        session.commit()
        return {"status": "ok"}

    @staticmethod
    def _delete_attachment(*, session, attach_target: Any, attachid: Any, orderid: Any, userid: Any) -> dict[str, Any]:
        if not (attach_target and attachid and orderid and userid):
            return {"status": "error", "error_mess": "WARN: No params"}

        try:
            web_attachment = session.query(Attachment).filter_by(id=int(attachid)).first()
            if web_attachment is not None:
                attach_path = web_attachment.path
                session.delete(web_attachment)

                base_dir_key = "QUESTION_ATTACHMENTS" if attach_target == "question" else "ANSWER_ATTACHMENTS"
                root_dir = get_config_value(base_dir_key)
                if root_dir:
                    file_path = os.path.join(str(root_dir), str(userid), str(orderid), str(attach_path))
                    try:
                        os.remove(file_path)
                    except OSError:
                        pass

            if attach_target == "question":
                order_attachment = session.query(OrderAttachment).filter_by(attachid=int(attachid)).first()
                if order_attachment is not None:
                    session.delete(order_attachment)
            elif attach_target == "answer":
                answer_attachment = session.query(AnswerAttachment).filter_by(attachid=int(attachid)).first()
                if answer_attachment is not None:
                    session.delete(answer_attachment)

            sync_record = session.query(SyncAttachments).filter_by(webattachid=int(attachid)).first()
            if sync_record is not None:
                telegram_attachment = session.query(TelegramAttachment).filter_by(id=sync_record.telattachid).first()
                if telegram_attachment is not None:
                    if attach_target == "question":
                        order_tg_attachment = session.query(OrderTelegramAttachment).filter_by(attachid=telegram_attachment.id).first()
                        if order_tg_attachment is not None:
                            session.delete(order_tg_attachment)
                    elif attach_target == "answer":
                        answer_tg_attachment = session.query(AnswerTelegramAttachment).filter_by(attachid=telegram_attachment.id).first()
                        if answer_tg_attachment is not None:
                            session.delete(answer_tg_attachment)
                    session.delete(telegram_attachment)
                session.delete(sync_record)

            session.commit()
            return {"status": "ok"}
        except Exception as exc:  # pragma: no cover - legacy-compatible envelope
            session.rollback()
            return {"status": "error", "error_mess": str(exc)}

    @staticmethod
    def get_statistics(payload: dict[str, Any], *, session) -> dict[str, Any] | StreamingResponse:
        delta = "7day" if int(payload.get("botimeperiod", 0)) == 7 else "30day"
        kind = payload.get("botstatskind")
        download_flag = int(payload.get("botdownloadflag", 0) or 0)

        if kind == "newusers":
            return AdminLegacyCompatService._new_users_stats(delta=delta, download_flag=download_flag, session=session)
        if kind == "phrazestats":
            return AdminLegacyCompatService._phrase_stats(delta=delta, download_flag=download_flag, session=session)
        if kind == "phrazesperday":
            return AdminLegacyCompatService._phrases_per_day_stats(delta=delta, download_flag=download_flag, session=session)

        return {"status": "error", "error_mess": "WARN: No params"}

    @staticmethod
    def _new_users_stats(*, delta: str, download_flag: int, session) -> dict[str, Any] | StreamingResponse:
        users_tel = session.query(UserTelegramInfo).all()
        users_count = session.query(UserTelegramInfo).count()

        records = [{"telid": user.tlgmid, "created_at": user.created_at} for user in users_tel]
        dataframe = pd.DataFrame(records)
        if dataframe.empty:
            return {"status": "ok", "info": {"new_user_data": [], "users_count": str(users_count)}}

        if download_flag != 1:
            dataframe = dataframe[dataframe["created_at"] > datetime.datetime.now(EAST_TZ) - pd.to_timedelta(delta)]

        dataframe["created_at"] = dataframe["created_at"].dt.strftime("%d-%m-%Y")
        grouped = dataframe.groupby(["created_at"]).agg({"telid": pd.Series.nunique}).reset_index()
        grouped["created_at"] = pd.to_datetime(grouped["created_at"], format="%d-%m-%Y")
        grouped.sort_values(by="created_at", inplace=True, ascending=True)
        grouped["created_at"] = grouped["created_at"].dt.strftime("%d-%m-%Y")

        if download_flag == 1:
            export_df = grouped.rename(columns={"created_at": "ДАТА", "telid": "КОЛ-ВО НОВЫХ ПОЛЬЗОВАТЕЛЕЙ"})
            return _excel_response(export_df, "newusers.xlsx")

        grouped = grouped.rename(columns={"created_at": "x", "telid": "y"})
        return {"status": "ok", "info": {"new_user_data": grouped.to_dict("records"), "users_count": str(users_count)}}

    @staticmethod
    def _phrase_stats(*, delta: str, download_flag: int, session) -> dict[str, Any] | StreamingResponse:
        phrases = session.query(TelPhrazeStats).all()
        records = [{"searchphraze": item.searchphrase, "created_at": item.created_at} for item in phrases]
        dataframe = pd.DataFrame(records)
        if dataframe.empty:
            return {"status": "ok", "info": {"infodata": []}}

        if download_flag != 1:
            dataframe = dataframe[dataframe["created_at"] > datetime.datetime.now(EAST_TZ) - pd.to_timedelta(delta)]

        dataframe["created_at"] = dataframe["created_at"].dt.strftime("%d-%m-%Y")
        dataframe["count"] = dataframe["searchphraze"]
        grouped = dataframe.groupby(["created_at", "searchphraze"]).agg({"count": "count"}).reset_index()
        grouped["created_at"] = pd.to_datetime(grouped["created_at"], format="%d-%m-%Y")
        grouped.sort_values(by="created_at", inplace=True, ascending=True)
        grouped["created_at"] = grouped["created_at"].dt.strftime("%d-%m-%Y")

        if download_flag == 1:
            export_df = grouped.rename(
                columns={"created_at": "ДАТА", "searchphraze": "ПОИСКОВЫЙ ЗАПРОС", "count": "КОЛ-ВО"}
            )
            return _excel_response(export_df, "phrazesstats.xlsx")

        return {"status": "ok", "info": {"infodata": grouped.to_dict("records")}}

    @staticmethod
    def _phrases_per_day_stats(*, delta: str, download_flag: int, session) -> dict[str, Any] | StreamingResponse:
        phrases = session.query(TelPhrazeStats).all()
        records = [{"searchphraze": item.searchphrase, "created_at": item.created_at} for item in phrases]
        dataframe = pd.DataFrame(records)
        if dataframe.empty:
            return {"status": "ok", "info": {"phrazes_data": []}}

        if download_flag != 1:
            dataframe = dataframe[dataframe["created_at"] > datetime.datetime.now(EAST_TZ) - pd.to_timedelta(delta)]

        dataframe["created_at"] = dataframe["created_at"].dt.strftime("%d-%m-%Y")
        grouped = dataframe.groupby(["created_at"]).agg({"searchphraze": "count"}).reset_index()
        grouped["created_at"] = pd.to_datetime(grouped["created_at"], format="%d-%m-%Y")
        grouped.sort_values(by="created_at", inplace=True, ascending=True)
        grouped["created_at"] = grouped["created_at"].dt.strftime("%d-%m-%Y")

        if download_flag == 1:
            export_df = grouped.rename(columns={"created_at": "ДАТА", "searchphraze": "КОЛ-ВО ЗАПРОСОВ"})
            return _excel_response(export_df, "perdayphrazestat.xlsx")

        grouped = grouped.rename(columns={"created_at": "x", "searchphraze": "y"})
        return {"status": "ok", "info": {"phrazes_data": grouped.to_dict("records")}}

    @staticmethod
    def build_bot_excel(payload: dict[str, Any]) -> dict[str, Any]:
        action = payload.get("action")
        chatid = payload.get("chatid")
        if not action or chatid in (None, ""):
            return {"status": "error", "error_mess": "WARN: No params"}

        tg_post(
            get_config_value("TEL_SENDMESS_URL"),
            json_body={
                "chat_id": chatid,
                "text": "⚠ <b>Запрос принят. Ожидайте ваш файл с результатами</b>",
                "parse_mode": "html",
            },
            timeout=(10.0, 40.0),
            socks_proxy=get_config_value("TEL_SOCKS_PROXY"),
        )

        env_name = get_config_value("FLASK_ENV")
        if action == "getfollowersexcel":
            from app.workers.tasks.getfollowers import get_followers_excel

            if env_name == "production":
                get_followers_excel.delay(chatid)
            else:
                get_followers_excel(chatid)
            return {"status": "ok"}

        if action == "getsuppinfo":
            from app.workers.tasks.getsuppinfo import get_supp_info

            if env_name == "production":
                get_supp_info.delay(chatid)
            else:
                get_supp_info(chatid)
            return {"status": "ok"}

        return {"status": "error", "error_mess": "WARN: No valid action param"}
