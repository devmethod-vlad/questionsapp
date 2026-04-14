"""Unified runtime settings source for environment-derived configuration."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any
from urllib.parse import quote_plus

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.constants import (
    BASE_ROLE,
    DEFAULT_RENDER_STATUSES,
    EXT_DICT,
    NULLROLE,
    NULLSPACE,
    QUESTION_STATUS,
    SHOW_ALL_SPACES_ITEM,
)


class AppSettings(BaseSettings):
    """Single settings object for app runtime modules."""

    model_config = SettingsConfigDict(
        extra="ignore",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
    )

    app_name: str = "questionsapp-fastapi"
    app_version: str = "1.0.0"
    api_prefix: str = Field(default="/eduportal/questions")
    enable_cors: bool = True
    cors_allow_origins: list[str] = ["*"]
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]
    include_request_id_header: bool = True

    prod: bool = Field(default=False, validation_alias="PROD")

    pg_user: str = Field(validation_alias="POSTGRES_USER")
    pg_pass: str = Field(validation_alias="POSTGRES_PASSWORD")
    pg_container: str = Field(validation_alias="PG_CONTAINER")
    pg_port: str = Field(default="5432", validation_alias="PG_PORT")
    pg_base: str = Field(validation_alias="PG_BASE")

    tel_token: str = Field(default="", validation_alias="TEL_TOKEN")
    tel_info_chat: str = Field(default="", validation_alias="TEL_INFO_CHAT")

    supp_db_host: str = Field(default="", validation_alias="SUPP_DB_HOST")
    supp_db_port: str = Field(default="", validation_alias="SUPP_DB_PORT")
    supp_db_sid: str = Field(default="", validation_alias="SUPP_DB_SID")
    supp_db_username: str = Field(default="", validation_alias="SUPP_DB_USERNAME")
    supp_db_pass: str = Field(default="", validation_alias="SUPP_DB_PASS")

    etd2_db_host: str = Field(default="", validation_alias="ETD2_DB_HOST")
    etd2_db_port: str = Field(default="", validation_alias="ETD2_DB_PORT")
    etd2_db_servicename: str = Field(default="", validation_alias="ETD2_DB_SERVICENAME")
    etd2_db_username: str = Field(default="", validation_alias="ETD2_DB_USERNAME")
    etd2_db_pass: str = Field(default="", validation_alias="ETD2_DB_PASS")

    iac_bot_token: str = Field(default="", validation_alias="IAC_BOT_TOKEN")
    tel_socks_proxy: str = Field(default="", validation_alias="TEL_SOCKS_PROXY")

    confluence_url: str = Field(default="", validation_alias="CONFLUENCE_BASE_URL")
    confl_bot_name: str = Field(default="", validation_alias="CONFLUENCE_BOT_NAME")
    confl_bot_pass: str = Field(default="", validation_alias="CONFL_BOT_PASS")
    confluence_spaceinfo_page: str = Field(default="", validation_alias="CONFLUENCE_SPACEINFO_PAGE")
    confluence_public_testpage_id: str = Field(default="", validation_alias="CONFLUENCE_PUBLIC_TESTPAGE_ID")

    questions_attachments: str = Field(validation_alias="QUESTIONS_ATTACHMENTS")
    questions_main_page: str = Field(default="", validation_alias="QUESTIONS_MAIN_PAGE")
    url_prefix: str = Field(default="/eduportal/questions", validation_alias="QUESTIONSAPP_URL_PREFIX")
    default_format: str = Field(default="UTF-8", validation_alias="DEFAULT_FORMAT")

    celery_result_backend: str | None = Field(default=None, validation_alias="CELERY_RESULT_BACKEND")
    celery_broker_url: str | None = Field(default=None, validation_alias="CELERY_BROKER_URL")

    max_content_length: int = 8 * 1000 * 1000
    sqlalchemy_engine_options: dict[str, Any] = {"pool_pre_ping": True}

    supp_parquet_data_dir: str = "/usr/src/data/suppinfo"
    supp_parquet_file_prefix: str = "supp"
    supp_parquet_file_ext: str = "gzip"
    supp_zip_data_dir: str = "/usr/src/data/suppinfo_zip"
    test_data_path: str = "/usr/src/data/"

    @property
    def sqlalchemy_database_uri(self) -> str:
        return (
            f"postgresql://{quote_plus(self.pg_user)}:{quote_plus(self.pg_pass)}@"
            f"{self.pg_container}:{self.pg_port}/{self.pg_base}"
        )

    @property
    def question_attachments_dir(self) -> str:
        return f"{self.questions_attachments}/orders/"

    @property
    def answer_attachments_dir(self) -> str:
        return f"{self.questions_attachments}/answers/"

    @property
    def tel_send_message_url(self) -> str:
        return f"https://api.telegram.org/bot{self.tel_token}/sendMessage"

    @property
    def flask_env(self) -> str:
        return "production" if self.prod else "development"

    @property
    def tel_info_list(self) -> list[int]:
        if self.prod:
            return [298333313, 313953337, 402905678]
        return [298333313]

    @property
    def tel_feedback_userlist(self) -> list[int]:
        return [298333313]

    @property
    def notify_self_order(self) -> bool:
        return not self.prod

    @property
    def web_app_ordershower(self) -> str:
        if self.prod:
            return "https://edu.emias.ru//edu-rest-api/questions/webappanonymviewer/"
        return "http://127.0.0.1:5000/eduportal/questions/webappanonymviewer/"

    def runtime_config_dict(self) -> dict[str, Any]:
        """Export a compatibility config mapping for Celery/runtime consumers."""

        return {
            "FLASK_ENV": self.flask_env,
            "PG_USER": self.pg_user,
            "PG_PASS": self.pg_pass,
            "PG_CONTAINER": self.pg_container,
            "PG_PORT": self.pg_port,
            "PG_BASE": self.pg_base,
            "MAX_CONTENT_LENGTH": self.max_content_length,
            "TEL_TOKEN": self.tel_token,
            "TEL_INFO_CHAT": self.tel_info_chat,
            "SUPP_DB_HOST": self.supp_db_host,
            "SUPP_DB_PORT": self.supp_db_port,
            "SUPP_DB_SID": self.supp_db_sid,
            "SUPP_DB_USERNAME": self.supp_db_username,
            "SUPP_DB_PASS": self.supp_db_pass,
            "ETD2_DB_HOST": self.etd2_db_host,
            "ETD2_DB_PORT": self.etd2_db_port,
            "ETD2_DB_SERVICENAME": self.etd2_db_servicename,
            "ETD2_DB_USERNAME": self.etd2_db_username,
            "ETD2_DB_PASS": self.etd2_db_pass,
            "IAC_BOT_TOKEN": self.iac_bot_token,
            "TEL_SOCKS_PROXY": self.tel_socks_proxy,
            "SUPP_PARQUET_DATA_DIR": self.supp_parquet_data_dir,
            "SUPP_PARQUET_FILE_PREFIX": self.supp_parquet_file_prefix,
            "SUPP_PARQUET_FILE_EXT": self.supp_parquet_file_ext,
            "SUPP_ZIP_DATA_DIR": self.supp_zip_data_dir,
            "SQLALCHEMY_DATABASE_URI": self.sqlalchemy_database_uri,
            "SQLALCHEMY_ENGINE_OPTIONS": self.sqlalchemy_engine_options,
            "CONFLUENCE_URL": self.confluence_url,
            "CONFL_BOT_NAME": self.confl_bot_name,
            "CONFL_BOT_PASS": self.confl_bot_pass,
            "CONFLUENCE_SPACEINFO_PAGE": self.confluence_spaceinfo_page,
            "CONFLUENCE_PUBLIC_TESTPAGE_ID": self.confluence_public_testpage_id,
            "TEST_DATA_PATH": self.test_data_path,
            "JS_FOLDER": self.js_folder,
            "CSS_FOLDER": self.css_folder,
            "IMGS_SRC": self.imgs_src,
            "FONTS_FOLDER": self.fonts_folder,
            "MAIN_JS_FOLDER": self.main_js_folder,
            "MAIN_CSS_FOLDER": self.main_css_folder,
            "MAIN_IMGS_FOLDER": self.main_imgs_folder,
            "WEBAPPAUTH_JS_FOLDER": self.webappauth_js_folder,
            "WEBAPPAUTH_CSS_FOLDER": self.webappauth_css_folder,
            "WEBAPPAUTH_IMGS_FOLDER": self.webappauth_imgs_folder,
            "WEBAPPMAIN_JS_FOLDER": self.webappmain_js_folder,
            "WEBAPPMAIN_CSS_FOLDER": self.webappmain_css_folder,
            "WEBAPPMAIN_IMGS_FOLDER": self.webappmain_imgs_folder,
            "WAPPANONYMVIEWER_JS_FOLDER": self.wappanonymviewer_js_folder,
            "WAPPANONYMVIEWER_CSS_FOLDER": self.wappanonymviewer_css_folder,
            "WAPPANONYMVIEWER_IMGS_FOLDER": self.wappanonymviewer_imgs_folder,
            "QUESTION_ATTACHMENTS": self.question_attachments_dir,
            "ANSWER_ATTACHMENTS": self.answer_attachments_dir,
            "TEL_SENDMESS_URL": self.tel_send_message_url,
            "QUESTIONS_MAIN_PAGE": self.questions_main_page,
            "URL_PREFIX": self.url_prefix,
            "BASE_ROLE": BASE_ROLE,
            "QUESTION_STATUS": QUESTION_STATUS,
            "DEFAULT_RENDER_STATUSES": DEFAULT_RENDER_STATUSES,
            "NULLSPACE": NULLSPACE,
            "NULLROLE": NULLROLE,
            "SHOW_ALL_SPACES_ITEM": SHOW_ALL_SPACES_ITEM,
            "EXT_DICT": EXT_DICT,
            "DEFAULT_FORMAT": self.default_format,
            "TEL_SEND_NEWMESS": True,
            "TEL_SEND_ANSWERMESS": True,
            "TEL_SEND_UPDTMESS": True,
            "TEL_SEND_MESSCLOSEXECTIME": True,
            "TEL_SEND_MESSINWORK": True,
            "TEL_SEND_MESSUSERCLOSED": True,
            "TEL_SEND_TOHELPMESS": True,
            "TEL_NOTIFY_FEEDBACK": True,
            "TEL_INFO_LIST": self.tel_info_list,
            "TEL_FEEDBACK_USERLIST": self.tel_feedback_userlist,
            "NOTIFY_SELF_ORDER": self.notify_self_order,
            "WEB_APP_ORDERSHOWER": self.web_app_ordershower,
        }

    @property
    def root_path(self) -> str:
        return os.getcwd()

    @property
    def js_folder(self) -> str:
        return os.path.join(self.root_path, "static/js/")

    @property
    def css_folder(self) -> str:
        return os.path.join(self.root_path, "static/css/")

    @property
    def imgs_src(self) -> str:
        return os.path.join(self.root_path, "static/imgs/")

    @property
    def fonts_folder(self) -> str:
        return os.path.join(self.root_path, "static/fonts/")

    @property
    def main_js_folder(self) -> str:
        return os.path.join(self.root_path, "static/main/js/")

    @property
    def main_css_folder(self) -> str:
        return os.path.join(self.root_path, "static/main/css/")

    @property
    def main_imgs_folder(self) -> str:
        return os.path.join(self.root_path, "static/main/imgs/")

    @property
    def webappauth_js_folder(self) -> str:
        return os.path.join(self.root_path, "static/webappauth/js/")

    @property
    def webappauth_css_folder(self) -> str:
        return os.path.join(self.root_path, "static/webappauth/css/")

    @property
    def webappauth_imgs_folder(self) -> str:
        return os.path.join(self.root_path, "static/webappauth/imgs/")

    @property
    def webappmain_js_folder(self) -> str:
        return os.path.join(self.root_path, "static/webappmain/js/")

    @property
    def webappmain_css_folder(self) -> str:
        return os.path.join(self.root_path, "static/webappmain/css/")

    @property
    def webappmain_imgs_folder(self) -> str:
        return os.path.join(self.root_path, "static/webappmain/imgs/")

    @property
    def wappanonymviewer_js_folder(self) -> str:
        return os.path.join(self.root_path, "static/webappanonymviewer/js/")

    @property
    def wappanonymviewer_css_folder(self) -> str:
        return os.path.join(self.root_path, "static/webappanonymviewer/css/")

    @property
    def wappanonymviewer_imgs_folder(self) -> str:
        return os.path.join(self.root_path, "static/webappanonymviewer/imgs/")


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    """Return cached app settings singleton."""

    return AppSettings()
