"""HTTP helper for Telegram Bot API integrations.

The helper keeps request/retry settings centralized and framework-agnostic so it
can be reused by FastAPI services, workers and legacy-compatible handlers.
"""

from __future__ import annotations

from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def tg_post(
    url: str,
    *,
    json_body: dict[str, Any] | None = None,
    data: dict[str, Any] | None = None,
    files: dict[str, Any] | None = None,
    timeout: tuple[float, float] = (10.0, 40.0),
    socks_proxy: str | None = None,
    total_retries: int = 3,
    connect_retries: int = 3,
    backoff_factor: float = 0.7,
    pool_connections: int = 20,
    pool_maxsize: int = 20,
) -> requests.Response:
    """Send a POST request to Telegram API with conservative retry policy."""

    if json_body is not None and data is not None:
        raise ValueError("Pass either 'json_body' or 'data', not both.")

    retry = Retry(
        total=total_retries,
        connect=connect_retries,
        read=0,
        status=0,
        backoff_factor=backoff_factor,
        allowed_methods=frozenset(["GET", "POST"]),
        raise_on_status=False,
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(
        max_retries=retry,
        pool_connections=pool_connections,
        pool_maxsize=pool_maxsize,
    )

    with requests.Session() as session:
        session.trust_env = False
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        if socks_proxy:
            session.proxies.update({"http": socks_proxy, "https": socks_proxy})

        return session.post(
            url,
            json=json_body,
            data=data,
            files=files,
            timeout=timeout,
            headers={"Expect": ""},
        )


__all__ = ["tg_post"]
