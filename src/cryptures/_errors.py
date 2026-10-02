"""Exception hierarchy for the Cryptures SDK.

Every exception raised by this library derives from :class:`CrypturesError`, so
``except CrypturesError`` catches all of them. Failed HTTP responses (any
non-2xx status) raise :class:`CrypturesApiError` or one of its status-specific
subclasses.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Mapping, Optional, Type

import httpx

__all__ = [
    "AuthenticationError",
    "BadRequestError",
    "ConflictError",
    "CrypturesApiError",
    "CrypturesConnectionError",
    "CrypturesError",
    "CrypturesResponseValidationError",
    "CrypturesTimeoutError",
    "GoneError",
    "InsufficientBalanceError",
    "InternalServerError",
    "NotFoundError",
    "PermissionDeniedError",
    "RateLimitError",
]


class CrypturesError(Exception):
    """Base class for every exception raised by the Cryptures SDK."""


class CrypturesApiError(CrypturesError):
    """The Cryptures API answered with a non-2xx HTTP status.

    Attributes:
        status_code: The HTTP status code of the response.
        code: Machine-readable error code (e.g. ``"forbidden_scope"``,
            ``"insufficient_balance"``), or ``None`` when the response body
            carried no code at all.
        message: Human-readable explanation of the failure.
        request_id: The request id to quote when contacting Cryptures support.
            Taken from ``error.requestId`` in the standard error envelope, or
            from the ``X-Request-ID`` response header when the body does not
            carry one.
        body: The decoded response body (parsed JSON when possible, otherwise
            the raw text), for inspecting fields beyond ``code``/``message``.
        headers: The response headers.

    Most failures use the standard Cryptures envelope
    ``{"error": {"code", "message", "requestId"}}``. A few operations are
    documented to return a different body on some failures (for example the
    card issuer's own ``{"status": "failure", "message", "code"}`` body on
    card operations, or ``{"statusCode", "errorCode", "message"}`` from
    ``exchange.rate``); those are mapped onto the same ``code``/``message``
    attributes, and the original body is always available as ``body``.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        code: Optional[str] = None,
        request_id: Optional[str] = None,
        body: Any = None,
        headers: Optional[Mapping[str, str]] = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.request_id = request_id
        self.body = body
        self.headers: Dict[str, str] = dict(headers or {})

    def __str__(self) -> str:
        parts = [f"HTTP {self.status_code}"]
        if self.code:
            parts.append(self.code)
        text = " ".join(parts) + f": {self.message}"
        if self.request_id:
            text += f" (request_id={self.request_id})"
        return text

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(status_code={self.status_code!r}, code={self.code!r}, "
            f"message={self.message!r}, request_id={self.request_id!r})"
        )


class BadRequestError(CrypturesApiError):
    """HTTP 400 -- the request failed validation (e.g. ``invalid_request``)."""


class AuthenticationError(CrypturesApiError):
    """HTTP 401 -- the ``x-api-key`` header is missing or not a valid token."""


class InsufficientBalanceError(CrypturesApiError):
    """HTTP 402 -- the project's balance cannot cover the charge (``insufficient_balance``)."""


class PermissionDeniedError(CrypturesApiError):
    """HTTP 403 -- e.g. ``forbidden_scope``, ``forbidden_card``, ``forbidden_tag``."""


class NotFoundError(CrypturesApiError):
    """HTTP 404 -- the resource (or chain coverage) does not exist."""


class ConflictError(CrypturesApiError):
    """HTTP 409 -- e.g. ``tag_name_taken``, ``check_in_progress``, ``idempotency_key_reused``."""


class GoneError(CrypturesApiError):
    """HTTP 410 -- e.g. ``report_expired``, ``session_deleted``."""


class RateLimitError(CrypturesApiError):
    """HTTP 429 -- ``rate_limited``; slow down and retry later."""


class InternalServerError(CrypturesApiError):
    """HTTP 5xx -- the API or an upstream it depends on failed."""


class CrypturesConnectionError(CrypturesError):
    """The request could not be completed at the network level (after any retries).

    Attributes:
        method: The HTTP method of the failed call, e.g. ``"GET"``.
        path_template: The documented path template of the failed call, e.g.
            ``"/api/v1/blockchain/wallet/{chain}"``.

    Neither the message nor any attribute carries the request URL, query
    string or headers: a URL can contain secrets (an EGLD mnemonic passed to
    ``wallet.derive_address`` is placed in the path) and the headers carry
    the API key. The underlying ``httpx`` exception is kept as
    ``__cause__``, with the same type and message but no ``request``.
    """

    def __init__(
        self, message: str, *, method: Optional[str] = None, path_template: Optional[str] = None
    ) -> None:
        super().__init__(message)
        self.method = method
        self.path_template = path_template


class CrypturesTimeoutError(CrypturesConnectionError):
    """The request timed out (after any retries)."""


class CrypturesResponseValidationError(CrypturesError):
    """A 2xx response body did not match the shape this SDK expects for the operation.

    The raw decoded body is available as ``body`` so it can still be used.
    """

    def __init__(self, message: str, *, status_code: int, body: Any) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.body = body


_STATUS_TO_ERROR: Dict[int, Type[CrypturesApiError]] = {
    400: BadRequestError,
    401: AuthenticationError,
    402: InsufficientBalanceError,
    403: PermissionDeniedError,
    404: NotFoundError,
    409: ConflictError,
    410: GoneError,
    429: RateLimitError,
}


def _str_or_none(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    return None


#: Longest ``code``/``message``/``request_id`` taken from a response body; the full body stays in ``body``.
MAX_ERROR_FIELD_CHARS = 1024
_TRUNCATED_SUFFIX = "... [truncated]"
#: C0/C1 control characters (CR, LF, ...) plus the Unicode line and paragraph separators.
_CONTROL_CHARS = {c: " " for c in [*range(0x00, 0x20), *range(0x7F, 0xA0), 0x2028, 0x2029]}


def sanitize_error_field(value: str) -> str:
    """Make a server-supplied string safe to embed in an exception message that will likely be logged.

    Control characters (CR, LF, ...) become spaces, so a malicious or buggy
    upstream cannot forge extra log lines, and the result is capped at
    :data:`MAX_ERROR_FIELD_CHARS` characters.
    """
    if len(value) > MAX_ERROR_FIELD_CHARS:
        value = value[:MAX_ERROR_FIELD_CHARS] + _TRUNCATED_SUFFIX
    return value.translate(_CONTROL_CHARS)


def _optional_field(value: Optional[str]) -> Optional[str]:
    return None if value is None else sanitize_error_field(value)


def error_from_response(response: httpx.Response, content: Optional[bytes] = None) -> CrypturesApiError:
    """Build the right :class:`CrypturesApiError` subclass for a failed response.

    ``content`` is the (possibly truncated) body when the response was read
    as a stream; by default the response's own content is used.
    """
    status = response.status_code
    header_request_id = response.headers.get("x-request-id")

    if content is None:
        content = response.content
    body: Any
    try:
        body = json.loads(content)
    except ValueError:
        body = content.decode(response.charset_encoding or "utf-8", errors="replace")

    code: Optional[str] = None
    message: Optional[str] = None
    request_id: Optional[str] = None

    if isinstance(body, dict):
        envelope = body.get("error")
        if isinstance(envelope, dict):
            # Standard Cryptures envelope: {"error": {"code", "message", "requestId"}}.
            code = _str_or_none(envelope.get("code"))
            message = _str_or_none(envelope.get("message"))
            request_id = _str_or_none(envelope.get("requestId"))
        else:
            # Documented non-envelope bodies: the card issuer's own
            # {"status": "failure", "message", "code"} and exchange.rate's
            # {"statusCode", "errorCode", "message"}.
            code = _str_or_none(body.get("code")) or _str_or_none(body.get("errorCode"))
            message = _str_or_none(body.get("message"))
            if message is None and isinstance(envelope, str):
                message = envelope

    if not message:
        if isinstance(body, str) and body.strip():
            message = body.strip()[:500]
        else:
            message = response.reason_phrase or f"HTTP {status}"

    error_cls = _STATUS_TO_ERROR.get(status)
    if error_cls is None:
        error_cls = InternalServerError if status >= 500 else CrypturesApiError

    return error_cls(
        sanitize_error_field(message),
        status_code=status,
        code=_optional_field(code),
        request_id=_optional_field(request_id or header_request_id),
        body=body,
        headers=response.headers,
    )
