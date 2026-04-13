"""Telegram integration gateway.

Centralizes Telegram Bot API calls with explicit timeout/retry policy and
structured logging hooks used by legacy tasks.
"""

from __future__ import annotations

import logging
from io import BytesIO

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class TelegramGateway:
    """HTTP gateway for Telegram Bot API."""

    def __init__(
        self,
        *,
        token: str,
        connect_timeout: float = 10.0,
        read_timeout: float = 40.0,
        retries: int = 3,
    ) -> None:
        self._token = token
        self._timeout = (connect_timeout, read_timeout)
        self._retries = retries

    @property
    def _base_url(self) -> str:
        return f"https://api.telegram.org/bot{self._token}"

    def _build_session(self) -> requests.Session:
        retry = Retry(
            total=self._retries,
            connect=self._retries,
            read=0,
            backoff_factor=0.3,
            allowed_methods=frozenset({"GET", "POST"}),
            status_forcelist=(429, 500, 502, 503, 504),
            raise_on_status=False,
            respect_retry_after_header=True,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session = requests.Session()
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def send_message(self, *, chat_id: int | str, text: str, parse_mode: str = "html", correlation_id: str | None = None) -> requests.Response:
        payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
        logger.info("Sending Telegram message", extra={"correlation_id": correlation_id, "chat_id": str(chat_id)})
        with self._build_session() as session:
            return session.post(f"{self._base_url}/sendMessage", data=payload, timeout=self._timeout)

    def send_document(self, *, chat_id: int | str, document: BytesIO, filename: str, correlation_id: str | None = None) -> requests.Response:
        document.name = filename
        logger.info("Sending Telegram document", extra={"correlation_id": correlation_id, "chat_id": str(chat_id), "filename": filename})
        with self._build_session() as session:
            return session.post(
                f"{self._base_url}/sendDocument?chat_id={chat_id}",
                files={"document": document},
                timeout=self._timeout,
            )
