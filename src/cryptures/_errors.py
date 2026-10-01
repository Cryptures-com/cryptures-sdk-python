"""Exception hierarchy for the Cryptures SDK.

Every exception raised by this library derives from :class:`CrypturesError`, so
``except CrypturesError`` catches all of them. Failed HTTP responses (any
non-2xx status) raise :class:`CrypturesApiError` or one of its status-specific
subclasses.
"""

from __future__ import annotations

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
    """The request could not be completed at the network level (after any retries)."""

    def __init__(self, message: str, *, request: Optional[httpx.Request] = None) -> None:
        super().__init__(message)
        self.request = request


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


def error_from_response(response: httpx.Response) -> CrypturesApiError:
    """Build the right :class:`CrypturesApiError` subclass for a failed response."""
    status = response.status_code
    header_request_id = response.headers.get("x-request-id")

    body: Any
    try:
        body = response.json()
    except ValueError:
        body = response.text

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
        message,
        status_code=status,
        code=code,
        request_id=request_id or header_request_id,
        body=body,
        headers=response.headers,
    )
