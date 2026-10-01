from __future__ import annotations

from ..._http import HttpClient, ResponseParser
from ...types.compliance import PresetList
from ...types.shared import WebhookRegistration, WebhookStatus
from .._base import APIResource
from .monitoring import ComplianceMonitoring
from .screening import ComplianceAml, ComplianceWalletScreening
from .sessions import ComplianceSessions

__all__ = [
    "Compliance",
    "ComplianceAml",
    "ComplianceMonitoring",
    "CompliancePresets",
    "ComplianceSessions",
    "ComplianceWalletScreening",
    "ComplianceWebhooks",
]

_PRESETS: ResponseParser[PresetList] = ResponseParser(PresetList)
_REGISTRATION: ResponseParser[WebhookRegistration] = ResponseParser(WebhookRegistration)
_STATUS: ResponseParser[WebhookStatus] = ResponseParser(WebhookStatus)


class CompliancePresets(APIResource):
    """Verification presets (workflows) usable with ``compliance.sessions.create``."""

    def list(self) -> PresetList:
        """List the standard, active verification presets (``compliance.presets.list``)."""
        return self._http.request_json("GET", "/api/v1/compliance/presets", parser=_PRESETS, retry_safe=True)


class ComplianceWebhooks(APIResource):
    """Compliance webhook registration (deliveries are signed with ``X-Verification-Signature``)."""

    def register(self, url: str) -> WebhookRegistration:
        """Register (or replace) the compliance webhook URL (``compliance.webhooks.register``).

        ``url`` must be a public ``https://`` URL. The returned ``secret`` is
        shown only once; re-registering rotates it.
        """
        return self._http.request_json(
            "POST",
            "/api/v1/compliance/webhooks/register",
            parser=_REGISTRATION,
            retry_safe=True,
            json={"url": url},
        )

    def status(self) -> WebhookStatus:
        """Read back the registered compliance webhook (``compliance.webhooks.status``)."""
        return self._http.request_json(
            "GET", "/api/v1/compliance/webhooks/status", parser=_STATUS, retry_safe=True
        )


class Compliance:
    """The ``compliance`` domain: KYC/KYB sessions, AML and wallet screening, monitoring."""

    def __init__(self, http: HttpClient) -> None:
        self.sessions = ComplianceSessions(http)
        self.presets = CompliancePresets(http)
        self.aml = ComplianceAml(http)
        self.wallet_screening = ComplianceWalletScreening(http)
        self.monitoring = ComplianceMonitoring(http)
        self.webhooks = ComplianceWebhooks(http)
