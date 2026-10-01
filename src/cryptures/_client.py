from __future__ import annotations

import os
from types import TracebackType
from typing import Mapping, Optional, Type, Union

import httpx

from ._http import DEFAULT_BASE_URL, DEFAULT_MAX_RETRIES, DEFAULT_TIMEOUT, HttpClient
from .resources.blockchain import Blockchain

__all__ = ["Cryptures"]

API_KEY_ENV_VAR = "CRYPTURES_API_KEY"


class Cryptures:
    """Synchronous client for the Cryptures API.

    Example::

        from cryptures import Cryptures

        client = Cryptures(api_key="...")
        balance = client.blockchain.data.get_balance("ETH", "0x...")

    Args:
        api_key: Your project's API token, sent as the ``x-api-key`` header.
            Falls back to the ``CRYPTURES_API_KEY`` environment variable.
        base_url: API base URL (default ``https://api.cryptures.com``).
        timeout: Per-request timeout in seconds (or an ``httpx.Timeout``).
        max_retries: Maximum automatic retries for retry-safe requests
            (see :class:`~cryptures._http.HttpClient` for the exact policy).
        http_client: Optional pre-configured ``httpx.Client`` (proxies,
            custom transports, ...). The SDK does not close a client you pass in.
        default_headers: Extra headers sent with every request.

    The client holds a connection pool: reuse one instance, and close it with
    :meth:`close` (or use it as a context manager) when done.
    """

    blockchain: Blockchain
    """Blockchain data, lookups, operations, wallets, contracts, fees, NFTs and storage."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = DEFAULT_BASE_URL,
        timeout: Union[float, httpx.Timeout, None] = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        *,
        http_client: Optional[httpx.Client] = None,
        default_headers: Optional[Mapping[str, str]] = None,
    ) -> None:
        resolved_key = api_key if api_key is not None else os.environ.get(API_KEY_ENV_VAR)
        if not resolved_key:
            raise ValueError(
                f"No API key provided. Pass api_key=... or set the {API_KEY_ENV_VAR} environment variable."
            )
        self._http = HttpClient(
            api_key=resolved_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            http_client=http_client,
            default_headers=default_headers,
        )
        self.blockchain = Blockchain(self._http)

    @property
    def base_url(self) -> str:
        return self._http.base_url

    @property
    def max_retries(self) -> int:
        return self._http.max_retries

    @property
    def timeout(self) -> Union[float, httpx.Timeout, None]:
        return self._http.timeout

    def close(self) -> None:
        """Close the underlying connection pool (unless you supplied ``http_client``)."""
        self._http.close()

    def __enter__(self) -> Cryptures:
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
        self.close()

    def __repr__(self) -> str:
        return f"Cryptures(base_url={self.base_url!r})"
