"""Client construction, configuration, request encoding and input validation."""

from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any, Callable

import httpx
import pytest

from cryptures import Cryptures, __version__

from .conftest import Recorder


def test_api_key_is_required(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CRYPTURES_API_KEY", raising=False)
    with pytest.raises(ValueError, match="API key"):
        Cryptures()


def test_api_key_falls_back_to_environment(monkeypatch: pytest.MonkeyPatch, recorder: Recorder) -> None:
    monkeypatch.setenv("CRYPTURES_API_KEY", "env_key")
    client = Cryptures(http_client=httpx.Client(transport=httpx.MockTransport(recorder.handler)))
    recorder.queue_json({"presets": []})

    client.compliance.presets.list()

    assert recorder.last.headers["x-api-key"] == "env_key"


def test_defaults() -> None:
    client = Cryptures("k")
    assert client.base_url == "https://api.cryptures.com"
    assert client.timeout == 30.0
    assert client.max_retries == 3
    client.close()


def test_custom_base_url_headers_and_timeout(recorder: Recorder) -> None:
    http_client = httpx.Client(transport=httpx.MockTransport(recorder.handler))
    client = Cryptures(
        "k",
        "https://sandbox.example.com/",
        timeout=5.0,
        http_client=http_client,
        default_headers={"X-Trace": "abc"},
    )
    recorder.queue_json({"presets": []})

    client.compliance.presets.list()

    request = recorder.last
    assert str(request.url) == "https://sandbox.example.com/api/v1/compliance/presets"
    assert request.headers["X-Trace"] == "abc"
    assert request.headers["user-agent"] == f"cryptures-python/{__version__}"
    assert request.headers["accept"] == "application/json"
    assert request.extensions["timeout"] == {"connect": 5.0, "read": 5.0, "write": 5.0, "pool": 5.0}


def test_api_key_cannot_be_overridden_by_default_headers(recorder: Recorder) -> None:
    http_client = httpx.Client(transport=httpx.MockTransport(recorder.handler))
    client = Cryptures("real", http_client=http_client, default_headers={"X-API-Key": "spoofed"})
    recorder.queue_json({"presets": []})
    client.compliance.presets.list()
    assert recorder.last.headers.get_list("x-api-key") == ["real"]


def test_context_manager_closes_owned_client() -> None:
    with Cryptures("k") as client:
        inner = client._http._client
        assert not inner.is_closed
    assert inner.is_closed


def test_supplied_http_client_is_not_closed(recorder: Recorder) -> None:
    http_client = httpx.Client(transport=httpx.MockTransport(recorder.handler))
    with Cryptures("k", http_client=http_client):
        pass
    assert not http_client.is_closed


def test_path_parameters_are_percent_encoded(client: Cryptures, recorder: Recorder) -> None:
    # An EGLD "xpub" is really a space-separated mnemonic; it must stay one path segment.
    recorder.queue_json({"address": "erd1"})

    client.blockchain.wallet.derive_address("EGLD", "word one/two", 3)

    assert recorder.last.url.raw_path == b"/api/v1/blockchain/wallet/EGLD/address/word%20one%2Ftwo/3"


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.blockchain.data.get_balance("", "0xabc"),
        lambda c: c.card.cards.get(""),
        lambda c: c.compliance.sessions.get(""),
    ],
)
def test_empty_path_parameter_is_rejected(
    client: Cryptures, recorder: Recorder, call: Callable[[Cryptures], Any]
) -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        call(client)
    assert recorder.requests == []


def test_derive_address_rejects_negative_index(client: Cryptures) -> None:
    with pytest.raises(ValueError):
        client.blockchain.wallet.derive_address("BTC", "xpub", -1)


def test_tags_update_requires_a_field(client: Cryptures) -> None:
    with pytest.raises(ValueError):
        client.card.tags.update("tag_1")


def test_set_tags_rejects_a_bare_string(client: Cryptures) -> None:
    with pytest.raises(TypeError):
        client.card.cards.set_tags("card_1", "Marketing")


def test_set_tags_sends_empty_list_explicitly(client: Cryptures, recorder: Recorder) -> None:
    recorder.queue_json({"tags": []})
    client.card.cards.set_tags("card_1", [])
    assert json.loads(recorder.last.content) == {"tags": []}


def test_empty_idempotency_key_is_rejected(client: Cryptures) -> None:
    with pytest.raises(ValueError):
        client.compliance.wallet_screening.create(address="0x0", chain="ETH", idempotency_key="")


def test_optional_fields_are_omitted_not_sent_as_null(client: Cryptures, recorder: Recorder) -> None:
    recorder.queue_json({"status": "success", "data": {"card_id": "c", "status": "active"}})

    client.card.cards.create(product_code="us_493_visa_atm", first_name="A", last_name="B", email="a@b.co")

    assert json.loads(recorder.last.content) == {
        "product_code": "us_493_visa_atm",
        "first_name": "A",
        "last_name": "B",
        "email": "a@b.co",
    }


def test_report_summary_accepts_datetimes(client: Cryptures, recorder: Recorder) -> None:
    import datetime as dt

    recorder.queue_json(
        {
            "range": {"from": "2026-01-01T00:00:00.000Z", "to": "2026-02-01T00:00:00.000Z"},
            "totals": {"funded_usd": 0, "withdrawn_usd": 0, "net_usd": 0, "card_count": 0},
            "unattributed": {"funded_usd": 0},
            "by_month": [],
            "by_type": [],
            "by_tag": [],
            "untagged": {"funded_usd": 0, "withdrawn_usd": 0, "net_usd": 0, "card_count": 0},
            "by_card": [],
        }
    )

    client.card.reports.summary(from_=dt.date(2026, 1, 1), to=dt.datetime(2026, 2, 1, tzinfo=dt.timezone.utc))

    assert dict(recorder.last.url.params) == {"from": "2026-01-01", "to": "2026-02-01T00:00:00+00:00"}


def test_storage_upload_sends_multipart_file(client: Cryptures, recorder: Recorder) -> None:
    recorder.queue_json({"ipfsHash": "bafy"}, status=201)

    client.blockchain.storage.upload_to_ipfs(b"hello world", filename="hello.txt", content_type="text/plain")

    request = recorder.last
    assert request.headers["content-type"].startswith("multipart/form-data; boundary=")
    body = request.content
    assert b'name="file"; filename="hello.txt"' in body
    assert b"Content-Type: text/plain" in body
    assert b"hello world" in body


def test_storage_upload_from_path_and_file_object(
    client: Cryptures, recorder: Recorder, tmp_path: Path
) -> None:
    file_path = tmp_path / "nft.json"
    file_path.write_bytes(b'{"name": "x"}')
    recorder.queue_json({"ipfsHash": "a"}, status=201)
    recorder.queue_json({"ipfsHash": "b"}, status=201)

    assert client.blockchain.storage.upload_to_ipfs(file_path).ipfsHash == "a"
    assert b'filename="nft.json"' in recorder.last.content

    assert client.blockchain.storage.upload_to_ipfs(io.BytesIO(b"raw")).ipfsHash == "b"
    assert b'filename="upload"' in recorder.last.content and b"raw" in recorder.last.content


def test_rpc_omits_params_when_not_given(client: Cryptures, recorder: Recorder) -> None:
    recorder.queue_json({"jsonrpc": "2.0", "id": 7, "error": {"code": -32601, "message": "Method not found"}})

    result = client.blockchain.operations.rpc("ETH", "eth_nope", id=7)

    assert json.loads(recorder.last.content) == {"jsonrpc": "2.0", "method": "eth_nope", "id": 7}
    assert result.error is not None and result.error.code == -32601
