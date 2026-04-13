import requests
from typing import Any, Dict, Optional
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

def _tg_post(
    url: str,
    *,
    json_body: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    files: Optional[Dict[str, Any]] = None,
    timeout: tuple[float, float] = (10.0, 40.0),
    socks_proxy: Optional[str] = None,
    total_retries: int = 3,
    connect_retries: int = 3,
    backoff_factor: float = 0.7,
    pool_connections: int = 20,
    pool_maxsize: int = 20,
) -> requests.Response:
    """
    Universal POST wrapper for Telegram API calls.

    The function is intentionally self-contained and does not rely on module-level
    globals such as a shared ``requests.Session`` or pre-created ``HTTPAdapter`` /
    ``Retry`` objects. This makes it easier to reuse in other projects and keeps
    the network behaviour explicit and predictable.

    What the function does
    ----------------------
    1. Creates a local ``requests.Session`` for the current request.
    2. Configures an ``HTTPAdapter`` with retry policy for transient connect-level
       network failures.
    3. Disables the ``Expect: 100-continue`` header because some proxies handle it
       poorly, especially for multipart uploads.
    4. Supports both ordinary POST requests and multipart/form-data requests with
       file uploads.
    5. Optionally applies the same SOCKS proxy to both HTTP and HTTPS traffic.

    Retry policy
    ------------
    By default the function retries only connection-stage failures (for example:
    proxy disconnects, TCP handshake problems, temporary network hiccups).

    It deliberately does *not* retry read timeouts or HTTP status codes by default,
    because Telegram may have already accepted and processed the request, and a
    blind retry could lead to duplicate messages or duplicate file uploads.

    Parameters
    ----------
    url:
        Full Telegram Bot API endpoint URL.

    json_body:
        JSON request body. Use for endpoints where you want to send JSON, for
        example ``sendMessage``.

    data:
        Form fields for ``application/x-www-form-urlencoded`` or multipart requests.
        Commonly used together with ``files``.

    files:
        Multipart files payload for Telegram endpoints such as ``sendDocument``,
        ``sendPhoto``, ``sendAudio`` or ``sendVideo``.

    timeout:
        Request timeout in the form ``(connect_timeout, read_timeout)``.

    socks_proxy:
        Optional SOCKS proxy URL.

        Examples:
            - ``socks5://user:pass@127.0.0.1:1080``
            - ``socks5h://user:pass@127.0.0.1:1080``

        ``socks5h://`` is usually preferable when you want DNS resolution to go
        through the proxy as well.

        Important:
            To use SOCKS proxies, the environment must have ``requests[socks]``
            installed.

    total_retries:
        Total retry count for the adapter.

    connect_retries:
        Retry count specifically for connection-stage failures.

    backoff_factor:
        Exponential backoff factor between retries.

    pool_connections / pool_maxsize:
        Adapter pool settings.

    Returns
    -------
    requests.Response
        Standard ``requests`` response object.

    Raises
    ------
    ValueError
        If both ``json_body`` and ``data`` are passed simultaneously.

    requests.RequestException
        Any network or transport-level exception raised by ``requests`` is not
        swallowed here and is propagated to the caller.
    """
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

    headers = {"Expect": ""}  # disable "100-continue"

    with requests.Session() as session:
        # Make behaviour deterministic between environments: do not implicitly use
        # HTTP(S)_PROXY / NO_PROXY from process environment.
        session.trust_env = False

        session.mount("https://", adapter)
        session.mount("http://", adapter)

        print("socks_proxy: ", socks_proxy)

        if socks_proxy:
            session.proxies.update(
                {
                    "http": socks_proxy,
                    "https": socks_proxy,
                }
            )

        return session.post(
            url,
            json=json_body,
            data=data,
            files=files,
            timeout=timeout,
            headers=headers,
        )