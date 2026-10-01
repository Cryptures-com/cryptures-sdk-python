from __future__ import annotations

from ..._http import ResponseParser
from ...types.shared import WebhookRegistration, WebhookStatus
from .._base import APIResource

__all__ = ["CardWebhooks"]

_REGISTRATION: ResponseParser[WebhookRegistration] = ResponseParser(WebhookRegistration)
_STATUS: ResponseParser[WebhookStatus] = ResponseParser(WebhookStatus)


class CardWebhooks(APIResource):
    """Card-domain webhook registration (deliveries are signed with ``X-Card-Signature``)."""

    def register(self, url: str) -> WebhookRegistration:
        """Register (or replace) the project's card-domain webhook URL (``card.webhooks.register``).

        ``url`` must be a public ``https://`` URL. The returned ``secret`` is
        shown only once and signs every delivery; re-registering rotates it.
        """
        return self._http.request_json(
            "POST", "/api/v1/card/webhooks/register", parser=_REGISTRATION, retry_safe=True, json={"url": url}
        )

    def status(self) -> WebhookStatus:
        """Read back the registered card-domain webhook (``card.webhooks.status``)."""
        return self._http.request_json("GET", "/api/v1/card/webhooks/status", parser=_STATUS, retry_safe=True)
