"""Models shared by more than one domain."""

from __future__ import annotations

from typing import Optional

from .._models import CrypturesModel

__all__ = ["WebhookRegistration", "WebhookStatus"]


class WebhookRegistration(CrypturesModel):
    """Result of registering (or re-registering) a webhook URL."""

    url: str
    """The registered URL, normalized."""
    secret: str
    """64-character hex signing secret. Returned once -- store it; it signs every future delivery."""


class WebhookStatus(CrypturesModel):
    """The currently registered webhook. The signing secret is never included."""

    registered: bool
    url: Optional[str]
    """The registered URL, or ``None`` if none is registered."""
    registered_at: Optional[str]
    """ISO 8601 timestamp of the latest (re-)registration, or ``None``."""
