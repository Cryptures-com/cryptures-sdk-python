"""Cursor and page-number iteration helpers."""

from __future__ import annotations

from typing import Any, Dict

from cryptures import Cryptures
from cryptures.types import BalanceTransaction, MonitoringSubscription, SessionSummary

from .cases_compliance import SUBSCRIPTION
from .conftest import Recorder


def _session(n: int) -> Dict[str, Any]:
    return {
        "session_id": f"s{n}",
        "external_user_id": "user_42",
        "preset_id": "p",
        "status": "Approved",
        "kind": "kyc",
        "created_at": "2026-09-18T10:51:32.000Z",
        "updated_at": "2026-09-18T10:55:53.000Z",
    }


def test_sessions_list_all_follows_next_cursor(client: Cryptures, recorder: Recorder) -> None:
    recorder.queue_json({"sessions": [_session(1), _session(2)], "next_cursor": "c2"})
    recorder.queue_json({"sessions": [_session(3)], "next_cursor": None})

    sessions = list(client.compliance.sessions.list_all(status="Approved", limit=2))

    assert [s.session_id for s in sessions] == ["s1", "s2", "s3"]
    assert all(isinstance(s, SessionSummary) for s in sessions)
    first, second = recorder.requests
    assert dict(first.url.params) == {"status": "Approved", "limit": "2"}
    assert dict(second.url.params) == {"status": "Approved", "limit": "2", "cursor": "c2"}


def test_sessions_list_all_is_lazy(client: Cryptures, recorder: Recorder) -> None:
    recorder.queue_json({"sessions": [_session(1)], "next_cursor": "c2"})

    iterator = client.compliance.sessions.list_all()
    assert recorder.requests == []
    assert next(iterator).session_id == "s1"
    assert len(recorder.requests) == 1


def test_monitoring_list_all_follows_next_cursor(client: Cryptures, recorder: Recorder) -> None:
    recorder.queue_json({"subscriptions": [SUBSCRIPTION], "next_cursor": "n1"})
    recorder.queue_json(
        {"subscriptions": [{**SUBSCRIPTION, "external_user_id": "user_43"}], "next_cursor": None}
    )

    subs = list(client.compliance.monitoring.list_all(status="active"))

    assert [s.external_user_id for s in subs] == ["user_42", "user_43"]
    assert all(isinstance(s, MonitoringSubscription) for s in subs)
    assert dict(recorder.requests[1].url.params) == {"status": "active", "cursor": "n1"}


def _ledger_row(n: int) -> Dict[str, Any]:
    return {
        "id": f"bl_{n}",
        "type": "card_fund_debit",
        "amount_usd": 1,
        "related_reference": None,
        "status": "completed",
        "created_at": "2026-08-29T00:00:01Z",
    }


def test_balance_list_all_transactions_walks_pages_until_total(client: Cryptures, recorder: Recorder) -> None:
    recorder.queue_json({"data": [_ledger_row(1), _ledger_row(2)], "page": 1, "limit": 2, "total": 3})
    recorder.queue_json({"data": [_ledger_row(3)], "page": 2, "limit": 2, "total": 3})

    rows = list(client.card.balance.list_all_transactions(limit=2))

    assert [r.id for r in rows] == ["bl_1", "bl_2", "bl_3"]
    assert all(isinstance(r, BalanceTransaction) for r in rows)
    assert [dict(r.url.params) for r in recorder.requests] == [
        {"page": "1", "limit": "2"},
        {"page": "2", "limit": "2"},
    ]


def test_balance_list_all_transactions_stops_on_empty_page(client: Cryptures, recorder: Recorder) -> None:
    recorder.queue_json({"data": [], "page": 1, "limit": 50, "total": 0})
    assert list(client.card.balance.list_all_transactions()) == []
    assert len(recorder.requests) == 1
