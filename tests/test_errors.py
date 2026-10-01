"""Error mapping: every non-2xx response raises CrypturesApiError with the documented fields."""

from __future__ import annotations

from typing import Any, Dict, Type

import httpx
import pytest

from cryptures import (
    AuthenticationError,
    BadRequestError,
    ConflictError,
    Cryptures,
    CrypturesApiError,
    CrypturesError,
    CrypturesResponseValidationError,
    GoneError,
    InsufficientBalanceError,
    InternalServerError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
)

from .conftest import Recorder


def envelope(code: str, message: str, request_id: str = "req_123") -> Dict[str, Any]:
    return {"error": {"code": code, "message": message, "requestId": request_id}}


@pytest.mark.parametrize(
    ("status", "code", "error_cls"),
    [
        (400, "invalid_request", BadRequestError),
        (401, "unauthenticated", AuthenticationError),
        (402, "insufficient_balance", InsufficientBalanceError),
        (403, "forbidden_scope", PermissionDeniedError),
        (404, "session_not_found", NotFoundError),
        (409, "tag_name_taken", ConflictError),
        (410, "report_expired", GoneError),
        (429, "rate_limited", RateLimitError),
        (418, "teapot", CrypturesApiError),
    ],
)
def test_standard_envelope_is_mapped(
    client: Cryptures, recorder: Recorder, status: int, code: str, error_cls: Type[CrypturesApiError]
) -> None:
    recorder.queue_json(envelope(code, "Something went wrong."), status=status)

    with pytest.raises(error_cls) as info:
        client.compliance.sessions.get("sess_1")

    err = info.value
    assert type(err) is error_cls
    assert isinstance(err, CrypturesApiError)
    assert isinstance(err, CrypturesError)
    assert err.status_code == status
    assert err.code == code
    assert err.message == "Something went wrong."
    assert err.request_id == "req_123"
    assert err.body == envelope(code, "Something went wrong.")
    assert code in str(err) and "req_123" in str(err)
    assert len(recorder.requests) == 1  # 4xx is never retried


def test_5xx_maps_to_internal_server_error(client: Cryptures, recorder: Recorder) -> None:
    client._http.max_retries = 0
    recorder.queue_json(envelope("upstream_error", "Upstream failed."), status=502)

    with pytest.raises(InternalServerError) as info:
        client.compliance.presets.list()

    assert info.value.status_code == 502
    assert info.value.code == "upstream_error"


def test_request_id_falls_back_to_header(client: Cryptures, recorder: Recorder) -> None:
    recorder.queue(
        httpx.Response(
            403,
            json={"error": {"code": "forbidden_card", "message": "No."}},
            headers={"X-Request-ID": "hdr_req_9"},
        )
    )

    with pytest.raises(PermissionDeniedError) as info:
        client.card.cards.get("card_x")

    assert info.value.code == "forbidden_card"
    assert info.value.request_id == "hdr_req_9"


def test_card_issuer_error_body_is_mapped(client: Cryptures, recorder: Recorder) -> None:
    # Card operations forward the issuer's own body verbatim (not the standard envelope).
    body = {"status": "failure", "message": "Card not found.", "code": "CARD_NOT_FOUND"}
    recorder.queue(httpx.Response(404, json=body, headers={"X-Request-ID": "req_card"}))

    with pytest.raises(NotFoundError) as info:
        client.card.cards.block("card_gone")

    assert info.value.code == "CARD_NOT_FOUND"
    assert info.value.message == "Card not found."
    assert info.value.request_id == "req_card"
    assert info.value.body == body


def test_exchange_rate_not_found_body_is_mapped(client: Cryptures, recorder: Recorder) -> None:
    # exchange.rate answers a well-formed but unpriced pair with 403 and its own body.
    body = {"statusCode": 403, "errorCode": "rate.not.found", "message": "No USD, XRP currency rates."}
    recorder.queue_json(body, status=403)

    with pytest.raises(PermissionDeniedError) as info:
        client.blockchain.data.get_exchange_rate("XRP")

    assert info.value.code == "rate.not.found"
    assert info.value.message == "No USD, XRP currency rates."


def test_non_json_error_body(client: Cryptures, recorder: Recorder) -> None:
    recorder.queue(httpx.Response(400, text="Bad Request: totalValue should not be empty"))

    with pytest.raises(BadRequestError) as info:
        client.blockchain.lookups.list_utxos("BTC", "34xp", total_value=0)

    assert info.value.code is None
    assert info.value.message == "Bad Request: totalValue should not be empty"
    assert info.value.request_id is None


def test_empty_error_body_uses_reason_phrase(client: Cryptures, recorder: Recorder) -> None:
    recorder.queue(httpx.Response(404))

    with pytest.raises(NotFoundError) as info:
        client.blockchain.data.check_address_security("0xabc")

    assert info.value.message == "Not Found"


def test_unexpected_success_shape_raises_validation_error(client: Cryptures, recorder: Recorder) -> None:
    recorder.queue_json({"unexpected": True})

    with pytest.raises(CrypturesResponseValidationError) as info:
        client.card.balance.get()

    assert info.value.status_code == 200
    assert info.value.body == {"unexpected": True}


def test_non_json_success_body_raises_validation_error(client: Cryptures, recorder: Recorder) -> None:
    recorder.queue(httpx.Response(200, text="<html>oops</html>"))

    with pytest.raises(CrypturesResponseValidationError):
        client.card.balance.get()


def test_unknown_response_fields_are_preserved(client: Cryptures, recorder: Recorder) -> None:
    recorder.queue_json({"balance_usd": 1.5, "updated_at": None, "currency": "USD"})

    balance = client.card.balance.get()

    assert balance.balance_usd == 1.5
    assert balance.model_extra == {"currency": "USD"}
    assert balance.to_dict() == {"balance_usd": 1.5, "currency": "USD"}
