"""Confluence integration gateway.

Provides a single place for Confluence client bootstrap and content fetch
with timeout/retry policy and correlation-id friendly logging.
"""

from __future__ import annotations

import logging

import requests
from atlassian import Confluence
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class ConfluenceGateway:
    """Gateway for Confluence REST API interactions."""

    def __init__(self, *, base_url: str, bearer_token: str, timeout: float = 20.0, retries: int = 3) -> None:
        self._base_url = base_url
        self._token = bearer_token
        self._timeout = timeout
        self._retries = retries

    def _build_session(self) -> requests.Session:
        retry = Retry(
            total=self._retries,
            connect=self._retries,
            read=0,
            backoff_factor=0.3,
            allowed_methods=frozenset({"GET", "POST", "PUT", "DELETE"}),
            status_forcelist=(429, 500, 502, 503, 504),
            raise_on_status=False,
            respect_retry_after_header=True,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session = requests.Session()
        session.headers.update({"Authorization": f"Bearer {self._token}"})
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def create_client(self, *, correlation_id: str | None = None) -> Confluence:
        logger.info("Creating Confluence client", extra={"correlation_id": correlation_id, "base_url": self._base_url})
        return Confluence(url=self._base_url, session=self._build_session())

    def get_storage_page(self, *, url: str, correlation_id: str | None = None) -> dict:
        logger.info("Fetching Confluence page storage", extra={"correlation_id": correlation_id, "url": url})
        with self._build_session() as session:
            response = session.get(url, timeout=self._timeout)
            response.raise_for_status()
            return response.json()
