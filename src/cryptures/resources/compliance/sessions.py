from __future__ import annotations

from typing import Any, Iterator, Literal, Mapping, Optional

from ..._http import ResponseParser, build_path
from ..._models import BinaryResponse
from ...types.compliance import (
    ComplianceReport,
    Session,
    SessionCreated,
    SessionList,
    SessionStatusUpdate,
    SessionSummary,
)
from .._base import APIResource, drop_none

__all__ = ["ComplianceSessions", "DocumentField"]

_CREATED: ResponseParser[SessionCreated] = ResponseParser(SessionCreated)
_SESSION: ResponseParser[Session] = ResponseParser(Session)
_SESSION_LIST: ResponseParser[SessionList] = ResponseParser(SessionList)
_STATUS_UPDATE: ResponseParser[SessionStatusUpdate] = ResponseParser(SessionStatusUpdate)
_REPORT: ResponseParser[ComplianceReport] = ResponseParser(ComplianceReport)

#: The document/image fields ``get_document`` accepts.
DocumentField = Literal[
    "portrait_image",
    "front_image",
    "back_image",
    "front_video",
    "back_video",
    "full_front_image",
    "full_back_image",
    "front_image_camera_front",
    "back_image_camera_front",
]


class ComplianceSessions(APIResource):
    """Identity (KYC) and business (KYB) verification sessions, documents and reports."""

    def create(
        self,
        *,
        preset_id: str,
        external_user_id: str,
        callback: Optional[str] = None,
        language: Optional[str] = None,
        metadata: Optional[Mapping[str, Any]] = None,
        expected_details: Optional[Mapping[str, str]] = None,
        contact_details: Optional[Mapping[str, str]] = None,
    ) -> SessionCreated:
        """Start a verification session and get its hosted link (``compliance.session.create``).

        Args:
            preset_id: A preset id from ``compliance.presets.list()``. A
                ``kyb`` preset verifies a company instead of a person.
            external_user_id: Your own identifier for the end user (max 200
                chars, no colon or control characters).
            callback: Public https URL the end user's browser returns to.
            language: Hosted page language, e.g. ``"en"``, ``"pt-BR"``.
            metadata: Free-form JSON object (max 2000 serialized characters).
            expected_details: ``first_name``, ``last_name``, ``date_of_birth``
                (``YYYY-MM-DD``) to check against the document.
            contact_details: The end user's contact details (``email``).
        """
        body = drop_none(
            preset_id=preset_id,
            external_user_id=external_user_id,
            callback=callback,
            language=language,
            metadata=dict(metadata) if metadata is not None else None,
            expected_details=dict(expected_details) if expected_details is not None else None,
            contact_details=dict(contact_details) if contact_details is not None else None,
        )
        return self._http.request_json(
            "POST", "/api/v1/compliance/sessions/create", parser=_CREATED, retry_safe=False, json=body
        )

    def get(self, session_id: str) -> Session:
        """Get a session's status and normalized result (``compliance.session.get``)."""
        path = build_path("/api/v1/compliance/sessions/{session_id}", session_id=session_id)
        return self._http.request_json("GET", path, parser=_SESSION, retry_safe=True)

    def list(
        self,
        *,
        status: Optional[str] = None,
        external_user_id: Optional[str] = None,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> SessionList:
        """List one page of sessions, newest first (``compliance.sessions.list``).

        Pass the returned ``next_cursor`` as ``cursor`` for the next page (it
        is ``None`` on the last page), or use :meth:`list_all`.

        Args:
            status: Only sessions in this status, e.g. ``"Approved"``.
            external_user_id: Only sessions for this end user.
            created_after: ISO-8601 date/timestamp (inclusive).
            created_before: ISO-8601 date/timestamp (exclusive).
            limit: Page size, 1-200 (default 50).
            cursor: ``next_cursor`` from the previous page.
        """
        params = {
            "status": status,
            "external_user_id": external_user_id,
            "created_after": created_after,
            "created_before": created_before,
            "limit": limit,
            "cursor": cursor,
        }
        return self._http.request_json(
            "GET", "/api/v1/compliance/sessions", parser=_SESSION_LIST, retry_safe=True, params=params
        )

    def list_all(
        self,
        *,
        status: Optional[str] = None,
        external_user_id: Optional[str] = None,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Iterator[SessionSummary]:
        """Iterate over every matching session, following ``next_cursor`` lazily."""
        cursor: Optional[str] = None
        while True:
            page = self.list(
                status=status,
                external_user_id=external_user_id,
                created_after=created_after,
                created_before=created_before,
                limit=limit,
                cursor=cursor,
            )
            yield from page.sessions
            if not page.next_cursor:
                return
            cursor = page.next_cursor

    def update_status(
        self, session_id: str, status: Literal["Approved", "Declined"], *, comment: Optional[str] = None
    ) -> SessionStatusUpdate:
        """Manually approve or decline a session (``compliance.session.status.update``).

        Repeating the same status is safe.

        Args:
            status: ``"Approved"`` or ``"Declined"``.
            comment: Optional note (max 500 printable characters).
        """
        path = build_path("/api/v1/compliance/sessions/{session_id}/status", session_id=session_id)
        return self._http.request_json(
            "PATCH",
            path,
            parser=_STATUS_UPDATE,
            retry_safe=True,
            json=drop_none(status=status, comment=comment),
        )

    def delete(self, session_id: str, *, privacy_erasure: Optional[bool] = None) -> None:
        """Delete a session (``compliance.session.delete``). Returns nothing (HTTP 204).

        Args:
            privacy_erasure: ``True`` to also request erasure of the end user's
                personal data. Only honored on the *first* successful delete.
        """
        path = build_path("/api/v1/compliance/sessions/{session_id}", session_id=session_id)
        self._http.request_no_content(
            "DELETE", path, retry_safe=True, params={"privacy_erasure": privacy_erasure}
        )

    def get_document(
        self, session_id: str, field: DocumentField, *, node_id: Optional[str] = None
    ) -> BinaryResponse:
        """Download a captured document photo, selfie or video (``compliance.session.documents.get``).

        Returns the raw bytes (``image/jpeg`` or ``video/mp4``).

        Args:
            field: Which document to fetch, e.g. ``"portrait_image"``.
            node_id: Disambiguates which result item to read when a session
                has more than one for this check.
        """
        path = build_path(
            "/api/v1/compliance/sessions/{session_id}/documents/{field}", session_id=session_id, field=field
        )
        return self._http.request_binary("GET", path, retry_safe=True, params={"node_id": node_id})

    def create_report(self, session_id: str) -> ComplianceReport:
        """Generate the verification report PDF (``compliance.session.report.create``).

        Kept for 7 days; generating again supersedes the previous report.
        """
        path = build_path("/api/v1/compliance/sessions/{session_id}/report", session_id=session_id)
        return self._http.request_json("POST", path, parser=_REPORT, retry_safe=True)

    def download_report(self, session_id: str) -> BinaryResponse:
        """Download the most recent report PDF (``compliance.session.report.download``)."""
        path = build_path("/api/v1/compliance/sessions/{session_id}/report", session_id=session_id)
        return self._http.request_binary("GET", path, retry_safe=True)
