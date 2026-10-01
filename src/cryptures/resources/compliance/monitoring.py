from __future__ import annotations

from typing import Iterator, Literal, Optional

from ..._http import ResponseParser
from ...types.compliance import MonitoringSubscription, MonitoringSubscriptionList
from .._base import APIResource

__all__ = ["ComplianceMonitoring", "EntityKind", "MonitoringStatus"]

_SUBSCRIPTION: ResponseParser[MonitoringSubscription] = ResponseParser(MonitoringSubscription)
_SUBSCRIPTION_LIST: ResponseParser[MonitoringSubscriptionList] = ResponseParser(MonitoringSubscriptionList)

EntityKind = Literal["user", "business"]
MonitoringStatus = Literal["active", "cancelled", "suspended_insufficient_balance"]


class ComplianceMonitoring(APIResource):
    """Ongoing AML monitoring of a person or company."""

    def enable(self, *, entity_kind: EntityKind, external_user_id: str) -> MonitoringSubscription:
        """Place a person/company under ongoing AML monitoring (``compliance.monitoring.enable``).

        Charges one year up front. Enabling an already-active entity is
        idempotent (no second charge).

        Args:
            entity_kind: ``"user"`` (KYC / person) or ``"business"`` (KYB / company).
            external_user_id: Your identifier, as used when it was screened.
        """
        return self._http.request_json(
            "POST",
            "/api/v1/compliance/monitoring",
            parser=_SUBSCRIPTION,
            retry_safe=True,
            json={"entity_kind": entity_kind, "external_user_id": external_user_id},
        )

    def disable(self, *, entity_kind: EntityKind, external_user_id: str) -> None:
        """Stop ongoing monitoring (``compliance.monitoring.disable``). Returns nothing (HTTP 204).

        The paid year is not refunded. Safe to repeat.
        """
        self._http.request_no_content(
            "DELETE",
            "/api/v1/compliance/monitoring",
            retry_safe=True,
            params={"entity_kind": entity_kind, "external_user_id": external_user_id},
        )

    def list(
        self,
        *,
        status: Optional[MonitoringStatus] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> MonitoringSubscriptionList:
        """List one page of monitoring subscriptions, newest first (``compliance.monitoring.list``).

        Args:
            status: Only subscriptions in this status.
            limit: Page size, 1-200 (default 50).
            cursor: ``next_cursor`` from the previous page.
        """
        return self._http.request_json(
            "GET",
            "/api/v1/compliance/monitoring",
            parser=_SUBSCRIPTION_LIST,
            retry_safe=True,
            params={"status": status, "limit": limit, "cursor": cursor},
        )

    def list_all(
        self, *, status: Optional[MonitoringStatus] = None, limit: Optional[int] = None
    ) -> Iterator[MonitoringSubscription]:
        """Iterate over every subscription, following ``next_cursor`` lazily."""
        cursor: Optional[str] = None
        while True:
            page = self.list(status=status, limit=limit, cursor=cursor)
            yield from page.subscriptions
            if not page.next_cursor:
                return
            cursor = page.next_cursor
