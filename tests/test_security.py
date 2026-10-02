"""Secrets (URL mnemonics, the API key) never end up in exceptions; server strings are made log-safe."""

from __future__ import annotations

import contextlib
import re
from typing import Any, Callable, Dict, Iterator, List, Set
from urllib.parse import quote, quote_plus

import httpx
import pytest

from cryptures import (
    BadRequestError,
    Cryptures,
    CrypturesConnectionError,
    CrypturesTimeoutError,
    InternalServerError,
)
from cryptures._errors import MAX_ERROR_FIELD_CHARS
from cryptures._http import MAX_ERROR_BODY_BYTES, ResponseParser, build_path

from .endpoint_cases import CASES, Case

MNEMONIC = "abandon ability able about above absent absorb abstract absurd abuse access accident"
API_KEY = "cr_live_5f2b9c1d7e8a4b6c9d0e1f2a3b4c5d6e"

#: Every form in which the secrets could show up.
SECRETS = [
    API_KEY,
    MNEMONIC,
    quote(MNEMONIC, safe=""),
    quote_plus(MNEMONIC),
    *MNEMONIC.split(),
]


def _leaky_transport_error(exc_type: Callable[..., httpx.TransportError]) -> Callable[[httpx.Request], Any]:
    """A worst-case transport failure: its message spells out the full URL and the API key."""

    def handler(request: httpx.Request) -> httpx.Response:
        raise exc_type(
            f"failed to reach {request.url} with key {request.headers['x-api-key']}", request=request
        )

    return handler


def _client(handler: Callable[[httpx.Request], Any], max_retries: int = 0) -> Cryptures:
    sdk = Cryptures(
        api_key=API_KEY,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        max_retries=max_retries,
    )
    sdk._http._sleep = lambda _: None
    return sdk


def _reachable_strings(obj: Any, seen: Set[int], depth: int = 0) -> Iterator[str]:
    """Every string reachable from ``obj``: str/repr, args, attributes, exception chain, nested values."""
    if id(obj) in seen or depth > 8:
        return
    seen.add(id(obj))
    if isinstance(obj, (str, bytes)):
        yield obj if isinstance(obj, str) else obj.decode("latin-1")
        return
    if obj is None or isinstance(obj, (int, float, bool)):
        return
    yield str(obj)
    yield repr(obj)
    if isinstance(obj, httpx.Request):  # must never be reachable, but check its contents if it is
        yield str(obj.url)
        yield from (f"{k}: {v}" for k, v in obj.headers.multi_items())
    children: List[Any] = []
    if isinstance(obj, BaseException):
        children += [*obj.args, obj.__cause__, obj.__context__]
        with contextlib.suppress(AttributeError, RuntimeError):
            children.append(obj.request)  # type: ignore[attr-defined]
    if isinstance(obj, dict):
        children += [*obj.keys(), *obj.values()]
    elif isinstance(obj, (list, tuple, set)):
        children += list(obj)
    if hasattr(obj, "__dict__") and not isinstance(obj, type):
        children += list(vars(obj).values())
    for child in children:
        yield from _reachable_strings(child, seen, depth + 1)


def assert_no_secrets(err: BaseException) -> None:
    for text in _reachable_strings(err, set()):
        for secret in SECRETS:
            assert secret not in text, f"{secret!r} leaked in {text!r}"


def test_connection_error_has_no_raw_request_or_api_key() -> None:
    client = _client(_leaky_transport_error(httpx.ConnectError))
    with pytest.raises(CrypturesConnectionError) as info:
        client.blockchain.wallet.generate("ETH")
    err = info.value

    assert_no_secrets(err)
    assert not hasattr(err, "request")
    assert err.method == "GET"
    assert err.path_template == "/api/v1/blockchain/wallet/{chain}"
    assert str(err).startswith("Connection error during GET /api/v1/blockchain/wallet/{chain}: ")
    assert "[REDACTED]" in str(err)
    # The httpx cause keeps its type and (scrubbed) message, but not the request.
    assert isinstance(err.__cause__, httpx.ConnectError)
    with pytest.raises(RuntimeError):
        err.__cause__.request  # noqa: B018
    assert err.__context__ is None or err.__context__ is err.__cause__


def test_wallet_generate_with_mnemonic_in_query_string_is_redacted() -> None:
    # The Python ``wallet.generate`` does not take a mnemonic, but the API's
    # ``wallet.generate`` accepts one as a query parameter; prove a query
    # string never leaks either.
    client = _client(_leaky_transport_error(httpx.ConnectError))
    path = build_path("/api/v1/blockchain/wallet/{chain}", chain="ETH")
    with pytest.raises(CrypturesConnectionError) as info:
        client._http.request_json(
            "GET", path, parser=ResponseParser(dict), retry_safe=False, params={"mnemonic": MNEMONIC}
        )
    assert_no_secrets(info.value)
    assert info.value.path_template == "/api/v1/blockchain/wallet/{chain}"


def test_egld_mnemonic_in_path_is_redacted() -> None:
    client = _client(_leaky_transport_error(httpx.ConnectError))
    with pytest.raises(CrypturesConnectionError) as info:
        client.blockchain.wallet.derive_address("EGLD", MNEMONIC, 0)
    assert_no_secrets(info.value)
    assert info.value.path_template == "/api/v1/blockchain/wallet/{chain}/address/{xpub}/{index}"


def test_timeout_after_retries_is_redacted() -> None:
    client = _client(_leaky_transport_error(httpx.ReadTimeout), max_retries=2)
    with pytest.raises(CrypturesTimeoutError) as info:
        client.blockchain.wallet.derive_address("EGLD", MNEMONIC, 7)
    assert_no_secrets(info.value)
    assert isinstance(info.value.__cause__, httpx.ReadTimeout)
    assert str(info.value) == (
        "Request timed out: GET /api/v1/blockchain/wallet/{chain}/address/{xpub}/{index}"
    )


def _template_regex(template: str) -> re.Pattern[str]:
    return re.compile("^" + re.sub(r"\\\{[^/]+?\\\}", "[^/]+", re.escape(template)) + "$")


@pytest.mark.parametrize("case", CASES, ids=[case.id for case in CASES])
def test_every_connection_error_names_only_the_path_template(case: Case) -> None:
    client = _client(_leaky_transport_error(httpx.ConnectError))
    with pytest.raises(CrypturesConnectionError) as info:
        case.call(client)
    err = info.value
    template = err.path_template
    assert template is not None
    assert err.method == case.method
    assert _template_regex(template).match(case.path), f"{template} does not describe {case.path}"
    if "{" not in template:
        assert template == case.path
    else:
        assert case.path not in str(err)
    assert "?" not in str(err)
    assert API_KEY not in str(err)


#: Whether each operation is retried automatically after a 5xx or network error
#: (without an Idempotency-Key). Identical in the Python, Go and JS SDKs.
RETRY_MATRIX: Dict[str, bool] = {
    # Never retried: repeating could duplicate a broadcast, a charge, a money
    # movement, or another irreversible side effect.
    "tx.send": False,
    "tx.broadcast": False,
    "rpc.gateway": False,
    "contract.token.deploy": False,
    "contract.token.mint": False,
    "contract.token.burn": False,
    "storage.ipfs.upload": False,
    "wallet.generate": False,
    "card.create": False,
    "card.fund": False,
    "card.withdraw": False,
    "card.setpin": False,
    "card.block": False,
    "card.unblock": False,
    "card.terminate": False,
    "card.tags.create": False,
    "compliance.session.create": False,
    "compliance.aml.check": False,
    "compliance.wallet_screening.create": False,
    # Retried: reads, and idempotent writes.
    "address.derive": True,
    "balance-history.get": True,
    "balance.batch": True,
    "balance.check": True,
    "block.get": True,
    "block.latest": True,
    "card.balance.get": True,
    "card.balance.transactions": True,
    "card.get": True,
    "card.list": True,
    "card.products.list": True,
    "card.reports.summary": True,
    "card.tags.delete": True,
    "card.tags.list": True,
    "card.tags.set": True,
    "card.tags.update": True,
    "card.transactions": True,
    "card.webhooks.register": True,
    "card.webhooks.status": True,
    "compliance.monitoring.disable": True,
    "compliance.monitoring.enable": True,
    "compliance.monitoring.list": True,
    "compliance.presets.list": True,
    "compliance.session.delete": True,
    "compliance.session.documents.get": True,
    "compliance.session.get": True,
    "compliance.session.report.create": True,
    "compliance.session.report.download": True,
    "compliance.session.status.update": True,
    "compliance.sessions.list": True,
    "compliance.wallet_screening.get": True,
    "compliance.webhooks.register": True,
    "compliance.webhooks.status": True,
    "exchange.rate": True,
    "exchange.rate.batch": True,
    "exchange.rate.contract": True,
    "fee.gas": True,
    "fee.get": True,
    "market.assets": True,
    "market.coin.info": True,
    "market.coin.markets": True,
    "market.coin.ohlcv": True,
    "market.coin.social": True,
    "market.exchanges": True,
    "market.exchanges.single": True,
    "market.global": True,
    "market.movers": True,
    "market.tickers": True,
    "market.tickers.single": True,
    "nft.collection.get": True,
    "nft.owner.get": True,
    "portfolio.get": True,
    "privatekey.derive": True,
    "security.address-check": True,
    "sentiment.fear-greed": True,
    "token.transfers": True,
    "tokens.get": True,
    "tx.hash": True,
    "tx.history": True,
    "utxo.batch": True,
    "utxo.list": True,
}


def test_retry_matrix_covers_every_operation() -> None:
    assert len(RETRY_MATRIX) == 80
    assert {case.operation_id for case in CASES} == set(RETRY_MATRIX)


@pytest.mark.parametrize("case", CASES, ids=[case.id for case in CASES])
def test_retry_matrix(case: Case) -> None:
    attempts: List[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        attempts.append(request)
        return httpx.Response(500, json={"error": {"code": "internal", "message": "boom"}})

    with pytest.raises(InternalServerError):
        case.call(_client(handler, max_retries=1))
    retryable = RETRY_MATRIX[case.operation_id] or "Idempotency-Key" in case.headers
    assert len(attempts) == (2 if retryable else 1), f"{case.id}: retryable={retryable}"


def test_error_fields_are_made_log_safe() -> None:
    long = "x" * 5000

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            400,
            json={
                "error": {
                    "code": "bad\r\ncode",
                    "message": "line one\r\nINFO forged log line\u2028" + long,
                    "requestId": "req\n1",
                }
            },
        )

    with pytest.raises(BadRequestError) as info:
        _client(handler).card.balance.get()
    err = info.value
    for text in (str(err), repr(err), err.message, err.code or "", err.request_id or ""):
        assert not any(ch in text for ch in "\r\n\u2028"), text
    assert err.message.startswith("line one  INFO forged log line ")
    assert err.message.endswith("... [truncated]")
    assert len(err.message) == MAX_ERROR_FIELD_CHARS + len("... [truncated]")
    assert err.code == "bad  code"
    assert err.request_id == "req 1"
    # The body is kept as received.
    assert err.body["error"]["message"].endswith(long)


def test_error_body_read_is_capped() -> None:
    huge = b"y" * (3 * MAX_ERROR_BODY_BYTES)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(502, content=huge, headers={"content-type": "text/plain"})

    with pytest.raises(InternalServerError) as info:
        _client(handler).card.balance.get()
    assert isinstance(info.value.body, str)
    assert len(info.value.body) == MAX_ERROR_BODY_BYTES
    assert len(info.value.message) <= 500
