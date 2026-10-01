"""Official Python SDK for the Cryptures API.

Blockchain infrastructure, crypto cards, and compliance in one client.
Full API reference: https://docs.cryptures.com/
"""

from . import types
from ._client import Cryptures
from ._errors import (
    AuthenticationError,
    BadRequestError,
    ConflictError,
    CrypturesApiError,
    CrypturesConnectionError,
    CrypturesError,
    CrypturesResponseValidationError,
    CrypturesTimeoutError,
    GoneError,
    InsufficientBalanceError,
    InternalServerError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
)
from ._models import BinaryResponse
from ._version import __version__

__all__ = [
    "AuthenticationError",
    "BadRequestError",
    "BinaryResponse",
    "ConflictError",
    "Cryptures",
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
    "__version__",
    "types",
]
