"""Retry policy: exponential backoff on network errors and 5xx for retry-safe calls; never on 4xx."""

from __future__ import annotations

from typing import Any, Callable

import httpx
import pytest

from cryptures import (
    BadRequestError,
    Cryptures,
    CrypturesConnectionError,
    CrypturesTimeoutError,
    InternalServerError,
    RateLimitError,
)

from .conftest import Recorder

ERR_500 = {"error": {"code": "internal_error", "message": "boom", "requestId": "req_500"}}
BALANCE = {"balance_usd": 10, "updated_at": None}


def test_get_is_retried_on_5xx_with_exponential_backoff(client: Cryptures, recorder: Recorder) -> None:
    recorder.queue(
        httpx.Response(500, json=ERR_500),
        httpx.Response(502, json=ERR_500),
        httpx.Response(503, json=ERR_500),
        httpx.Response(200, json=BALANCE),
    )

    balance = client.card.balance.get()

    assert balance.balance_usd == 10
    assert len(recorder.requests) == 4
    assert len(recorder.sleeps) == 3
    # ~0.25s, ~0.5s, ~1s: exponential with at most 25% downward jitter.
    for attempt, delay in enumerate(recorder.sleeps):
        base = 0.25 * 2**attempt
        assert 0.75 * base <= delay <= base


def test_retries_are_exhausted_after_max_retries(client: Cryptures, recorder: Recorder) -> None:
    recorder.queue(*[httpx.Response(500, json=ERR_500) for _ in range(4)])

    with pytest.raises(InternalServerError) as info:
        client.card.balance.get()

    assert info.value.request_id == "req_500"
    assert len(recorder.requests) == 4  # 1 attempt + max_retries (3)


@pytest.mark.parametrize("status", [400, 401, 403, 404, 409, 429])
def test_4xx_is_never_retried(client: Cryptures, recorder: Recorder, status: int) -> None:
    recorder.queue(httpx.Response(status, json={"error": {"code": "x", "message": "y", "requestId": "r"}}))

    with pytest.raises(Exception) as info:
        client.card.balance.get()

    assert getattr(info.value, "status_code", None) == status
    assert len(recorder.requests) == 1
    assert recorder.sleeps == []


def test_429_raises_rate_limit_error_without_retry(client: Cryptures, recorder: Recorder) -> None:
    recorder.queue(
        httpx.Response(429, json={"error": {"code": "rate_limited", "message": "slow", "requestId": "r"}})
    )
    with pytest.raises(RateLimitError):
        client.compliance.presets.list()
    assert len(recorder.requests) == 1


def test_network_error_is_retried_then_succeeds(client: Cryptures, recorder: Recorder) -> None:
    recorder.queue(
        httpx.ReadError("connection reset"),
        httpx.ReadTimeout("slow"),
        httpx.Response(200, json=BALANCE),
    )

    assert client.card.balance.get().balance_usd == 10
    assert len(recorder.requests) == 3
    assert len(recorder.sleeps) == 2


def test_network_error_exhausted_raises_connection_error(client: Cryptures, recorder: Recorder) -> None:
    recorder.queue(*[httpx.ConnectError("refused") for _ in range(4)])

    with pytest.raises(CrypturesConnectionError) as info:
        client.card.balance.get()

    assert not isinstance(info.value, CrypturesTimeoutError)
    assert len(recorder.requests) == 4


def test_timeout_exhausted_raises_timeout_error(client: Cryptures, recorder: Recorder) -> None:
    recorder.queue(*[httpx.ReadTimeout("slow") for _ in range(4)])

    with pytest.raises(CrypturesTimeoutError):
        client.card.balance.get()

    assert len(recorder.requests) == 4


@pytest.mark.parametrize(
    "call",
    [
        pytest.param(lambda c: c.card.cards.fund("card_1", 10), id="card.fund"),
        pytest.param(
            lambda c: c.card.cards.create(
                product_code="p", first_name="a", last_name="b", email="e@x.io", initial_load=10
            ),
            id="card.create",
        ),
        pytest.param(lambda c: c.blockchain.operations.broadcast("BTC", "00ff"), id="tx.broadcast"),
        pytest.param(lambda c: c.blockchain.operations.send_transaction("ETH", {"to": "0x"}), id="tx.send"),
        pytest.param(
            lambda c: c.blockchain.contracts.burn_token(
                chain="ETH", contract_address="0x", amount="1", from_private_key="k"
            ),
            id="contract.token.burn",
        ),
        pytest.param(
            lambda c: c.compliance.aml.check(external_user_id="u", full_name="n"), id="aml.check-no-key"
        ),
    ],
)
def test_non_idempotent_calls_are_not_retried_after_reaching_the_api(
    client: Cryptures, recorder: Recorder, call: Callable[[Cryptures], Any]
) -> None:
    # The API documents that a 5xx on these does NOT mean nothing happened.
    recorder.queue(httpx.Response(500, json=ERR_500))
    with pytest.raises(InternalServerError):
        call(client)
    assert len(recorder.requests) == 1

    recorder.queue(httpx.ReadTimeout("slow"))
    with pytest.raises(CrypturesTimeoutError):
        call(client)
    assert len(recorder.requests) == 2
    assert recorder.sleeps == []


def test_non_idempotent_call_is_retried_when_connection_never_established(
    client: Cryptures, recorder: Recorder
) -> None:
    recorder.queue(
        httpx.ConnectError("refused"),
        httpx.Response(
            200, json={"status": "success", "data": {"card_id": "c", "amount": 1, "display_amount": 1}}
        ),
    )

    result = client.card.cards.fund("c", 1)

    assert result.data.card_id == "c"
    assert len(recorder.requests) == 2
    assert recorder.requests[0].content == recorder.requests[1].content


def test_idempotency_key_makes_screening_retryable(client: Cryptures, recorder: Recorder) -> None:
    body = {
        "check_id": "chk_1",
        "session_id": None,
        "external_user_id": "u",
        "status": "Approved",
        "result": {"features": ["AML"], "results": [], "warnings": []},
        "created_at": "2026-09-25T09:00:00.000Z",
    }
    recorder.queue(
        httpx.Response(502, json=ERR_500),
        httpx.Response(200, json=body, headers={"Idempotent-Replay": "true"}),
    )

    result = client.compliance.aml.check(external_user_id="u", full_name="n", idempotency_key="key-1")

    assert result.check_id == "chk_1"
    assert result.session_id is None
    assert len(recorder.requests) == 2
    assert all(r.headers["Idempotency-Key"] == "key-1" for r in recorder.requests)


def test_max_retries_zero_disables_retries(recorder: Recorder) -> None:
    http_client = httpx.Client(transport=httpx.MockTransport(recorder.handler))
    client = Cryptures(api_key="k", max_retries=0, http_client=http_client)
    recorder.queue(httpx.Response(503, json=ERR_500))

    with pytest.raises(InternalServerError):
        client.card.balance.get()

    assert len(recorder.requests) == 1


def test_retry_after_header_is_honoured_on_5xx(client: Cryptures, recorder: Recorder) -> None:
    recorder.queue(
        httpx.Response(503, json=ERR_500, headers={"Retry-After": "2"}),
        httpx.Response(200, json=BALANCE),
    )

    client.card.balance.get()

    assert recorder.sleeps == [2.0]


def test_bad_request_is_not_retried_even_for_get(client: Cryptures, recorder: Recorder) -> None:
    recorder.queue(
        httpx.Response(400, json={"error": {"code": "invalid_request", "message": "x", "requestId": "r"}})
    )
    with pytest.raises(BadRequestError):
        client.compliance.sessions.list(limit=1000)
    assert len(recorder.requests) == 1


def test_misconfiguration_errors_are_not_retried(client: Cryptures, recorder: Recorder) -> None:
    recorder.queue(httpx.UnsupportedProtocol("Request URL is missing an 'http://' or 'https://' protocol."))
    with pytest.raises(CrypturesConnectionError):
        client.card.balance.get()
    assert len(recorder.requests) == 1
    assert recorder.sleeps == []
