from __future__ import annotations

import json
from typing import Any, Callable, Dict, Iterator, List, Optional, Union

import httpx
import pytest

from cryptures import Cryptures

API_KEY = "test_api_key_123"
BASE_URL = "https://api.cryptures.com"

Responder = Callable[[httpx.Request], httpx.Response]


class Recorder:
    """Records every request the SDK sends and answers with queued responses."""

    def __init__(self) -> None:
        self.requests: List[httpx.Request] = []
        self._responses: List[Union[httpx.Response, Exception, Responder]] = []
        self.sleeps: List[float] = []

    def queue(self, *responses: Union[httpx.Response, Exception, Responder]) -> None:
        self._responses.extend(responses)

    def queue_json(self, body: Any, status: int = 200, headers: Optional[Dict[str, str]] = None) -> None:
        self.queue(httpx.Response(status, json=body, headers=headers))

    def handler(self, request: httpx.Request) -> httpx.Response:
        request.read()
        self.requests.append(request)
        if not self._responses:
            raise AssertionError(f"Unexpected request: {request.method} {request.url}")
        item = self._responses.pop(0)
        if isinstance(item, Exception):
            raise item
        if callable(item) and not isinstance(item, httpx.Response):
            return item(request)
        return item

    @property
    def last(self) -> httpx.Request:
        assert self.requests, "no request was sent"
        return self.requests[-1]

    def last_json(self) -> Any:
        return json.loads(self.last.content)


@pytest.fixture
def recorder() -> Recorder:
    return Recorder()


@pytest.fixture
def client(recorder: Recorder) -> Iterator[Cryptures]:
    http_client = httpx.Client(transport=httpx.MockTransport(recorder.handler))
    sdk = Cryptures(api_key=API_KEY, http_client=http_client)
    sdk._http._sleep = recorder.sleeps.append  # never actually sleep in tests
    yield sdk
    sdk.close()
    http_client.close()
