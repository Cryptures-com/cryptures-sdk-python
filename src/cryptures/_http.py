"""The HTTP layer shared by every resource: auth, retries, and error mapping."""

from __future__ import annotations

import email.utils
import random
import time
from typing import Any, Callable, Dict, Generic, Mapping, Optional, Tuple, TypeVar, Union
from urllib.parse import quote

import httpx
from pydantic import TypeAdapter, ValidationError

from ._errors import (
    CrypturesConnectionError,
    CrypturesResponseValidationError,
    CrypturesTimeoutError,
    error_from_response,
)
from ._models import BinaryResponse
from ._version import __version__

__all__ = [
    "DEFAULT_BASE_URL",
    "DEFAULT_MAX_RETRIES",
    "DEFAULT_TIMEOUT",
    "HttpClient",
    "ResponseParser",
    "build_path",
    "build_query",
]

T = TypeVar("T")

DEFAULT_BASE_URL = "https://api.cryptures.com"
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 3

#: First retry waits ~0.25s, then ~0.5s, ~1s, ... (capped), with jitter.
INITIAL_RETRY_DELAY = 0.25
MAX_RETRY_DELAY = 8.0
#: Upper bound for honouring a server-sent ``Retry-After`` on a 5xx.
MAX_RETRY_AFTER = 30.0

FileTuple = Tuple[str, bytes, str]


class ResponseParser(Generic[T]):
    """Validates a decoded JSON body into ``T`` (built lazily, then cached)."""

    def __init__(self, tp: Any) -> None:
        self._tp = tp
        self._adapter: Optional[TypeAdapter[T]] = None

    def parse(self, data: Any) -> T:
        if self._adapter is None:
            self._adapter = TypeAdapter(self._tp)
        return self._adapter.validate_python(data)


def build_path(template: str, **params: Union[str, int]) -> str:
    """Fill ``{name}`` placeholders in ``template``, percent-encoding each value.

    Every value is encoded as a single path segment (``/`` included), and an
    empty value is rejected: it would silently route the call to a different
    endpoint.
    """
    encoded: Dict[str, str] = {}
    for name, value in params.items():
        if isinstance(value, bool) or not isinstance(value, (str, int)):
            raise TypeError(f"Path parameter {name!r} must be a str or int, got {type(value).__name__}")
        text = str(value)
        if text == "":
            raise ValueError(f"Path parameter {name!r} must not be empty")
        encoded[name] = quote(text, safe="")
    return template.format(**encoded)


def build_query(params: Mapping[str, Any]) -> Dict[str, Union[str, int, float]]:
    """Drop ``None`` values and render booleans the way the API expects (``true``/``false``)."""
    query: Dict[str, Union[str, int, float]] = {}
    for key, value in params.items():
        if value is None:
            continue
        if isinstance(value, bool):
            query[key] = "true" if value else "false"
        else:
            query[key] = value
    return query


class HttpClient:
    """Sends authenticated requests to the Cryptures API.

    Retry policy (exponential backoff with jitter, at most ``max_retries``
    extra attempts):

    * A failure to *establish* a connection (DNS, refused connection, connect
      timeout) is retried for every operation: the request never reached the
      API, so nothing can have happened twice.
    * Any other network error (read timeout, dropped connection) and any 5xx
      response are retried only for operations that are safe to repeat --
      reads, and writes the API documents as idempotent or that carry an
      ``Idempotency-Key``. Operations that move money or broadcast a
      transaction (``tx.send``, ``tx.broadcast``, token deploy/mint/burn,
      ``card.create``/``fund``/``withdraw``, ...) are never re-sent after the
      request may have reached the API: the API documents that a 5xx there
      does not mean nothing happened.
    * 4xx responses are never retried.
    """

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: Union[float, httpx.Timeout, None] = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        http_client: Optional[httpx.Client] = None,
        default_headers: Optional[Mapping[str, str]] = None,
    ) -> None:
        if not api_key:
            raise ValueError("api_key must be a non-empty string")
        if max_retries < 0:
            raise ValueError("max_retries must be >= 0")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self._owns_client = http_client is None
        self._client = http_client if http_client is not None else httpx.Client(timeout=timeout)
        self._default_headers: Dict[str, str] = {
            "Accept": "application/json",
            "User-Agent": f"cryptures-python/{__version__}",
        }
        if default_headers:
            self._default_headers.update(default_headers)
        # Indirection so tests can avoid real sleeping.
        self._sleep: Callable[[float], None] = time.sleep

    # ------------------------------------------------------------------ public

    def request_json(
        self,
        method: str,
        path: str,
        *,
        parser: ResponseParser[T],
        retry_safe: bool,
        params: Optional[Mapping[str, Any]] = None,
        json: Any = None,
        files: Optional[Mapping[str, FileTuple]] = None,
        headers: Optional[Mapping[str, str]] = None,
    ) -> T:
        response = self.send(
            method, path, retry_safe=retry_safe, params=params, json=json, files=files, headers=headers
        )
        try:
            data = response.json()
        except ValueError as exc:
            raise CrypturesResponseValidationError(
                f"Expected a JSON body from {method} {path}, got {response.headers.get('content-type')!r}",
                status_code=response.status_code,
                body=response.text,
            ) from exc
        try:
            return parser.parse(data)
        except ValidationError as exc:
            raise CrypturesResponseValidationError(
                f"Unexpected response shape from {method} {path}: {exc}",
                status_code=response.status_code,
                body=data,
            ) from exc

    def request_no_content(
        self,
        method: str,
        path: str,
        *,
        retry_safe: bool,
        params: Optional[Mapping[str, Any]] = None,
    ) -> None:
        self.send(method, path, retry_safe=retry_safe, params=params)

    def request_binary(
        self,
        method: str,
        path: str,
        *,
        retry_safe: bool,
        params: Optional[Mapping[str, Any]] = None,
    ) -> BinaryResponse:
        response = self.send(method, path, retry_safe=retry_safe, params=params, accept="*/*")
        return BinaryResponse(response.content, headers=response.headers)

    def send(
        self,
        method: str,
        path: str,
        *,
        retry_safe: bool,
        params: Optional[Mapping[str, Any]] = None,
        json: Any = None,
        files: Optional[Mapping[str, FileTuple]] = None,
        headers: Optional[Mapping[str, str]] = None,
        accept: Optional[str] = None,
    ) -> httpx.Response:
        """Send a request with retries; return the 2xx response or raise."""
        request = self._build_request(
            method, path, params=params, json=json, files=files, headers=headers, accept=accept
        )
        attempt = 0
        while True:
            try:
                response = self._client.send(request)
            except httpx.TransportError as exc:
                if attempt < self.max_retries and self._should_retry_exception(exc, retry_safe):
                    self._sleep(self._retry_delay(attempt, None))
                    attempt += 1
                    continue
                if isinstance(exc, httpx.TimeoutException):
                    raise CrypturesTimeoutError(
                        f"Request timed out: {method} {path}", request=request
                    ) from exc
                raise CrypturesConnectionError(
                    f"Connection error during {method} {path}: {exc}", request=request
                ) from exc

            if response.is_success:
                response.read()
                return response

            response.read()
            if response.status_code >= 500 and retry_safe and attempt < self.max_retries:
                self._sleep(self._retry_delay(attempt, response))
                response.close()
                attempt += 1
                continue
            raise error_from_response(response)

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    # ----------------------------------------------------------------- helpers

    def _build_request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Mapping[str, Any]],
        json: Any,
        files: Optional[Mapping[str, FileTuple]],
        headers: Optional[Mapping[str, str]],
        accept: Optional[str],
    ) -> httpx.Request:
        merged = httpx.Headers(self._default_headers)
        if accept is not None:
            merged["Accept"] = accept
        if headers:
            merged.update(headers)
        merged["x-api-key"] = self.api_key
        query = build_query(params) if params else None
        return self._client.build_request(
            method,
            self.base_url + path,
            params=query or None,
            json=json,
            files=dict(files) if files else None,
            headers=merged,
            timeout=self.timeout,
        )

    @staticmethod
    def _should_retry_exception(exc: httpx.TransportError, retry_safe: bool) -> bool:
        # Misconfiguration (e.g. a base_url without http/https) never succeeds on retry.
        if isinstance(exc, (httpx.UnsupportedProtocol, httpx.LocalProtocolError)):
            return False
        # Nothing was sent if the connection could not be established.
        if isinstance(exc, (httpx.ConnectError, httpx.ConnectTimeout, httpx.PoolTimeout)):
            return True
        return retry_safe

    @staticmethod
    def _retry_delay(attempt: int, response: Optional[httpx.Response]) -> float:
        delay: float = min(INITIAL_RETRY_DELAY * (2.0**attempt), MAX_RETRY_DELAY)
        delay *= 1 - 0.25 * random.random()  # up to 25% jitter, never longer than the base
        if response is not None:
            retry_after = _parse_retry_after(response.headers.get("retry-after"))
            if retry_after is not None:
                delay = max(delay, min(retry_after, MAX_RETRY_AFTER))
        return delay


def _parse_retry_after(value: Optional[str]) -> Optional[float]:
    if not value:
        return None
    try:
        seconds = float(value)
    except ValueError:
        try:
            parsed = email.utils.parsedate_to_datetime(value)
        except (TypeError, ValueError, IndexError):
            return None
        if parsed is None or parsed.tzinfo is None:
            return None
        seconds = parsed.timestamp() - time.time()
    return max(seconds, 0.0)
