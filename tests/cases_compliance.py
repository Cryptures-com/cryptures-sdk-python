"""Endpoint cases for the compliance domain (17 operations)."""

from __future__ import annotations

from typing import List

from cryptures import BinaryResponse
from cryptures import types as t

from ._case import Case
from .cases_card import WEBHOOK_REGISTRATION

SESSION_ID = "a1b2c3d4-e5f6-4789-a012-3456789abcde"
SUBSCRIPTION = {
    "entity_kind": "user",
    "external_user_id": "user_42",
    "status": "active",
    "enabled_at": "2026-09-25T09:00:00.000Z",
    "next_renewal_at": "2027-09-25T09:00:00.000Z",
    "cancelled_at": None,
    "created_at": "2026-09-25T09:00:00.000Z",
    "updated_at": "2026-09-25T09:00:00.000Z",
}
WALLET_SCREENING = {
    "check_id": "chk_7c1d9e2f-3a4b-4c5d-8e6f-0a1b2c3d4e5f",
    "address": "0x0000000000000000000000000000000000000000",
    "chain": "ETH",
    "result": {
        "severity": "LOW",
        "risk_score": 12,
        "sanctions_hit": False,
        "pep_counterparty": False,
        "dominant_risk_category": "exchange",
        "risk_factors": [
            {
                "category": "exchange",
                "direction": "outgoing",
                "exposure_type": "direct",
                "percentage": 40,
                "is_high_risk": False,
            }
        ],
    },
    "screened_at": "2026-09-25T09:00:00.000Z",
}

COMPLIANCE_CASES: List[Case] = [
    # ==================================================== compliance.sessions
    Case(
        "compliance.session.create",
        "compliance.sessions.create",
        lambda c: c.compliance.sessions.create(
            preset_id="preset_af36",
            external_user_id="user_42",
            callback="https://example.com/done",
            language="en",
            metadata={"plan": "pro"},
            expected_details={"first_name": "Jane", "last_name": "Doe", "date_of_birth": "1990-01-01"},
            contact_details={"email": "jane@example.com"},
        ),
        "POST",
        "/api/v1/compliance/sessions/create",
        status=201,
        json={
            "preset_id": "preset_af36",
            "external_user_id": "user_42",
            "callback": "https://example.com/done",
            "language": "en",
            "metadata": {"plan": "pro"},
            "expected_details": {"first_name": "Jane", "last_name": "Doe", "date_of_birth": "1990-01-01"},
            "contact_details": {"email": "jane@example.com"},
        },
        response={
            "session_id": SESSION_ID,
            "url": "https://verify.example.com/session/xyz",
            "status": "Not Started",
        },
        check=lambda r: isinstance(r, t.SessionCreated) and r.status == "Not Started",
    ),
    Case(
        "compliance.session.get",
        "compliance.sessions.get",
        lambda c: c.compliance.sessions.get(SESSION_ID),
        "GET",
        f"/api/v1/compliance/sessions/{SESSION_ID}",
        response={
            "session_id": SESSION_ID,
            "status": "Approved",
            "external_user_id": "user_42",
            "kind": "kyc",
            "features": ["ID_VERIFICATION", "LIVENESS", "FACE_MATCH", "AML"],
            "results": [
                {
                    "feature": "ID_VERIFICATION",
                    "status": "Approved",
                    "document_type": "Identity Card",
                    "name": "Jane Doe",
                    "date_of_birth": "1990-01-01",
                    "issuing_state": "ESP",
                },
                {"feature": "LIVENESS", "status": "Approved", "method": "ACTIVE_3D", "score": 95.4},
                {"feature": "AML", "status": "Approved", "total_hits": 0, "entity_type": "person"},
            ],
            "warnings": [],
            "document_urls": {
                "portrait_image": f"https://api.cryptures.com/api/v1/compliance/sessions/{SESSION_ID}/documents/portrait_image"
            },
        },
        check=lambda r: (
            isinstance(r, t.Session)
            and r.results[1].score == 95.4
            and "portrait_image" in (r.document_urls or {})
        ),
    ),
    Case(
        "compliance.sessions.list",
        "compliance.sessions.list",
        lambda c: c.compliance.sessions.list(
            status="Approved",
            external_user_id="user_42",
            created_after="2026-09-01T00:00:00Z",
            created_before="2026-10-01T00:00:00Z",
            limit=50,
            cursor="abc",
        ),
        "GET",
        "/api/v1/compliance/sessions",
        query={
            "status": "Approved",
            "external_user_id": "user_42",
            "created_after": "2026-09-01T00:00:00Z",
            "created_before": "2026-10-01T00:00:00Z",
            "limit": "50",
            "cursor": "abc",
        },
        response={
            "sessions": [
                {
                    "session_id": SESSION_ID,
                    "external_user_id": "user_42",
                    "preset_id": "preset_af36",
                    "status": "Approved",
                    "kind": "kyc",
                    "created_at": "2026-09-18T10:51:32.000Z",
                    "updated_at": "2026-09-18T10:55:53.000Z",
                }
            ],
            "next_cursor": None,
        },
        check=lambda r: (
            isinstance(r, t.SessionList) and r.next_cursor is None and r.sessions[0].kind == "kyc"
        ),
    ),
    Case(
        "compliance.presets.list",
        "compliance.presets.list",
        lambda c: c.compliance.presets.list(),
        "GET",
        "/api/v1/compliance/presets",
        response={"presets": [{"id": "preset_af36", "label": "Standard KYC", "kind": "kyc"}]},
        check=lambda r: isinstance(r, t.PresetList) and r.presets[0].label == "Standard KYC",
    ),
    Case(
        "compliance.session.documents.get",
        "compliance.sessions.get_document",
        lambda c: c.compliance.sessions.get_document(SESSION_ID, "portrait_image", node_id="feature_t_ocr"),
        "GET",
        f"/api/v1/compliance/sessions/{SESSION_ID}/documents/portrait_image",
        query={"node_id": "feature_t_ocr"},
        raw_response=b"\xff\xd8\xff\xe0jpeg-bytes",
        response_headers={"content-type": "image/jpeg"},
        check=lambda r: (
            isinstance(r, BinaryResponse)
            and r.content.startswith(b"\xff\xd8")
            and r.content_type == "image/jpeg"
        ),
    ),
    Case(
        "compliance.webhooks.register",
        "compliance.webhooks.register",
        lambda c: c.compliance.webhooks.register("https://example.com/webhooks/compliance"),
        "POST",
        "/api/v1/compliance/webhooks/register",
        json={"url": "https://example.com/webhooks/compliance"},
        response={**WEBHOOK_REGISTRATION, "url": "https://example.com/webhooks/compliance"},
        check=lambda r: isinstance(r, t.WebhookRegistration) and r.url.endswith("/compliance"),
    ),
    Case(
        "compliance.webhooks.status",
        "compliance.webhooks.status",
        lambda c: c.compliance.webhooks.status(),
        "GET",
        "/api/v1/compliance/webhooks/status",
        response={"registered": False, "url": None, "registered_at": None},
        check=lambda r: isinstance(r, t.WebhookStatus) and r.registered is False and r.url is None,
    ),
    Case(
        "compliance.session.status.update",
        "compliance.sessions.update_status",
        lambda c: c.compliance.sessions.update_status(SESSION_ID, "Approved", comment="Reviewed."),
        "PATCH",
        f"/api/v1/compliance/sessions/{SESSION_ID}/status",
        json={"status": "Approved", "comment": "Reviewed."},
        response={"session_id": SESSION_ID, "status": "Approved"},
        check=lambda r: isinstance(r, t.SessionStatusUpdate) and r.status == "Approved",
    ),
    Case(
        "compliance.session.delete",
        "compliance.sessions.delete",
        lambda c: c.compliance.sessions.delete(SESSION_ID, privacy_erasure=True),
        "DELETE",
        f"/api/v1/compliance/sessions/{SESSION_ID}",
        query={"privacy_erasure": "true"},
        status=204,
        check=lambda r: r is None,
    ),
    Case(
        "compliance.aml.check",
        "compliance.aml.check",
        lambda c: c.compliance.aml.check(
            external_user_id="user_42",
            full_name="Jane Doe",
            date_of_birth="1990-01-01",
            nationality="ES",
            entity_type="person",
            idempotency_key="idem-123",
        ),
        "POST",
        "/api/v1/compliance/aml/checks",
        status=201,
        json={
            "external_user_id": "user_42",
            "full_name": "Jane Doe",
            "date_of_birth": "1990-01-01",
            "nationality": "ES",
            "entity_type": "person",
        },
        headers={"Idempotency-Key": "idem-123"},
        response={
            "check_id": "chk_0b5e",
            "session_id": SESSION_ID,
            "external_user_id": "user_42",
            "status": "Approved",
            "result": {
                "features": ["AML"],
                "results": [
                    {"feature": "AML", "status": "Approved", "total_hits": 0, "entity_type": "person"}
                ],
                "warnings": [],
            },
            "created_at": "2026-09-25T09:00:00.000Z",
        },
        check=lambda r: isinstance(r, t.AmlCheck) and r.result.results[0].total_hits == 0,
    ),
    Case(
        "compliance.wallet_screening.create",
        "compliance.wallet_screening.create",
        lambda c: c.compliance.wallet_screening.create(
            address="0x0000000000000000000000000000000000000000", chain="ETH", idempotency_key="idem-9"
        ),
        "POST",
        "/api/v1/compliance/wallet-screenings",
        status=201,
        json={"address": "0x0000000000000000000000000000000000000000", "chain": "ETH"},
        headers={"Idempotency-Key": "idem-9"},
        response=WALLET_SCREENING,
        check=lambda r: (
            isinstance(r, t.WalletScreening)
            and r.result.severity == "LOW"
            and r.result.risk_factors[0].percentage == 40
        ),
    ),
    Case(
        "compliance.wallet_screening.get",
        "compliance.wallet_screening.get",
        lambda c: c.compliance.wallet_screening.get("chk_7c1d9e2f-3a4b-4c5d-8e6f-0a1b2c3d4e5f"),
        "GET",
        "/api/v1/compliance/wallet-screenings/chk_7c1d9e2f-3a4b-4c5d-8e6f-0a1b2c3d4e5f",
        response=WALLET_SCREENING,
        check=lambda r: isinstance(r, t.WalletScreening) and r.result.sanctions_hit is False,
    ),
    Case(
        "compliance.monitoring.enable",
        "compliance.monitoring.enable",
        lambda c: c.compliance.monitoring.enable(entity_kind="user", external_user_id="user_42"),
        "POST",
        "/api/v1/compliance/monitoring",
        status=201,
        json={"entity_kind": "user", "external_user_id": "user_42"},
        response=SUBSCRIPTION,
        check=lambda r: (
            isinstance(r, t.MonitoringSubscription) and r.status == "active" and r.cancelled_at is None
        ),
    ),
    Case(
        "compliance.monitoring.disable",
        "compliance.monitoring.disable",
        lambda c: c.compliance.monitoring.disable(entity_kind="user", external_user_id="user_42"),
        "DELETE",
        "/api/v1/compliance/monitoring",
        query={"entity_kind": "user", "external_user_id": "user_42"},
        status=204,
        check=lambda r: r is None,
    ),
    Case(
        "compliance.monitoring.list",
        "compliance.monitoring.list",
        lambda c: c.compliance.monitoring.list(status="active", limit=10, cursor="cur1"),
        "GET",
        "/api/v1/compliance/monitoring",
        query={"status": "active", "limit": "10", "cursor": "cur1"},
        response={"subscriptions": [SUBSCRIPTION], "next_cursor": None},
        check=lambda r: (
            isinstance(r, t.MonitoringSubscriptionList) and r.subscriptions[0].entity_kind == "user"
        ),
    ),
    Case(
        "compliance.session.report.create",
        "compliance.sessions.create_report",
        lambda c: c.compliance.sessions.create_report(SESSION_ID),
        "POST",
        f"/api/v1/compliance/sessions/{SESSION_ID}/report",
        status=201,
        response={
            "report_id": "rep_3d5f",
            "session_id": SESSION_ID,
            "generated_at": "2026-09-25T09:00:00.000Z",
            "expires_at": "2026-10-02T09:00:00.000Z",
            "size_bytes": 18234,
            "download_url": f"https://api.cryptures.com/api/v1/compliance/sessions/{SESSION_ID}/report",
        },
        check=lambda r: isinstance(r, t.ComplianceReport) and r.size_bytes == 18234,
    ),
    Case(
        "compliance.session.report.download",
        "compliance.sessions.download_report",
        lambda c: c.compliance.sessions.download_report(SESSION_ID),
        "GET",
        f"/api/v1/compliance/sessions/{SESSION_ID}/report",
        raw_response=b"%PDF-1.7 report",
        response_headers={
            "content-type": "application/pdf",
            "content-disposition": f'attachment; filename="verification-report-{SESSION_ID}.pdf"',
        },
        check=lambda r: (
            isinstance(r, BinaryResponse)
            and r.content.startswith(b"%PDF")
            and r.filename == f"verification-report-{SESSION_ID}.pdf"
        ),
    ),
]
