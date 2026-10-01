"""Every API operation: correct method/path/query/headers/body sent, response parsed correctly."""

from __future__ import annotations

import json

import httpx
import pytest

from cryptures import Cryptures

from .conftest import API_KEY, Recorder
from .endpoint_cases import CASES, Case


@pytest.mark.parametrize("case", CASES, ids=[case.id for case in CASES])
def test_endpoint(case: Case, client: Cryptures, recorder: Recorder) -> None:
    if case.raw_response is not None:
        recorder.queue(httpx.Response(case.status, content=case.raw_response, headers=case.response_headers))
    elif case.status == 204:
        recorder.queue(httpx.Response(204))
    else:
        recorder.queue_json(case.response, status=case.status)

    result = case.call(client)

    assert len(recorder.requests) == 1
    request = recorder.last
    assert request.method == case.method
    assert request.url.scheme == "https"
    assert request.url.host == "api.cryptures.com"
    assert request.url.raw_path.decode().split("?")[0] == case.path
    assert dict(request.url.params) == case.query
    assert len(request.url.params.multi_items()) == len(case.query), "a query parameter was sent twice"

    assert request.headers["x-api-key"] == API_KEY
    assert request.headers["user-agent"].startswith("cryptures-python/")
    for name, value in case.headers.items():
        assert request.headers[name] == value
    if "Idempotency-Key" not in case.headers:
        assert "idempotency-key" not in request.headers

    content_type = request.headers.get("content-type", "")
    if case.json is not None:
        assert content_type == "application/json"
        assert json.loads(request.content) == case.json
    elif content_type.startswith("multipart/form-data"):
        pass  # covered in detail by test_storage_upload_sends_multipart_file
    else:
        assert request.content == b"", f"unexpected request body: {request.content!r}"

    assert case.check(result), f"unexpected parsed result: {result!r}"
