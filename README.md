# Cryptures Python SDK

[![CI](https://github.com/Cryptures-com/cryptures-sdk-python/actions/workflows/ci.yml/badge.svg)](https://github.com/Cryptures-com/cryptures-sdk-python/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)

Official Python SDK for the [Cryptures](https://cryptures.com) API — blockchain infrastructure, crypto cards, and compliance in one client.

- **Blockchain** — balances, transaction history, blocks, tokens, NFTs, market data, wallets, fees, transaction send/broadcast, JSON-RPC, token contracts, and IPFS storage.
- **Cards** — issue and manage virtual cards, fund and withdraw, tags, reports, the project balance ledger, and card webhooks.
- **Compliance** — KYC/KYB verification sessions, standalone AML screening, wallet risk screening, ongoing monitoring, reports, and compliance webhooks.

Every one of the API's 80 operations has a typed method, with [Pydantic v2](https://docs.pydantic.dev/) models for every response.

Full API reference: **https://docs.cryptures.com/**

## Installation

```bash
pip install cryptures
```

Requires Python 3.9+. Dependencies: [`httpx`](https://www.python-httpx.org/) and [`pydantic`](https://docs.pydantic.dev/) v2.

## Authentication

Every request is authenticated with your project's API token, sent as the `x-api-key` header. Cryptures issues the token when your project is provisioned; it is shown only once, so store it somewhere safe.

Pass it to the client directly, or set the `CRYPTURES_API_KEY` environment variable:

```python
from cryptures import Cryptures

client = Cryptures(api_key="your-api-token")

# or, with CRYPTURES_API_KEY set in the environment:
client = Cryptures()
```

A key can be scoped to specific domains and categories. A request outside your key's scope fails with `403 forbidden_scope` (raised as `PermissionDeniedError`).

## Quickstart

```python
from cryptures import Cryptures

with Cryptures(api_key="your-api-token") as client:
    balance = client.blockchain.data.get_balance("ETH", "0xae680ed83baf08a8028118bd19859f8a0e744cc6")
    print(balance)

    products = client.card.cards.list_products()
    for product in products.products:
        print(product.product_code, product.display_name)
```

The client keeps a connection pool, so create one instance and reuse it. Close it when you are done, either with `client.close()` or by using it as a context manager.

## Usage by domain

The client mirrors the API's own structure: `client.<domain>.<category>.<method>()`.

| Namespace | Operations |
| --- | --- |
| `client.blockchain.data` | balances, batch balances, balance history, portfolio, transaction history, TRC-20 transfers, address security check, exchange rates, Fear & Greed index, market data |
| `client.blockchain.lookups` | transaction by hash, block by hash/height, latest TRON block, token metadata, UTXOs |
| `client.blockchain.operations` | build-sign-send a transaction, broadcast a signed transaction, JSON-RPC passthrough |
| `client.blockchain.wallet` | generate a wallet, derive an address, derive a private key |
| `client.blockchain.contracts` | deploy, mint, and burn fungible tokens |
| `client.blockchain.fee` | recommended network fees, gas estimates |
| `client.blockchain.nft` | NFTs in a collection, owners of a token |
| `client.blockchain.storage` | upload a file to IPFS |
| `client.card.cards` | create, get, list, fund, withdraw, block, unblock, terminate, set PIN, set tags, transactions, products |
| `client.card.balance` | project balance, balance ledger |
| `client.card.tags` | list, create, update, delete tags |
| `client.card.reports` | funding/withdrawal summary report |
| `client.card.webhooks` | register a webhook, read webhook status |
| `client.compliance.sessions` | create, get, list, update status, delete, documents, reports |
| `client.compliance.presets` | list verification presets |
| `client.compliance.aml` | standalone AML screening |
| `client.compliance.wallet_screening` | screen a blockchain address, read a stored screening |
| `client.compliance.monitoring` | enable, disable, and list ongoing monitoring |
| `client.compliance.webhooks` | register a webhook, read webhook status |

### Blockchain

```python
from cryptures.types import BalanceSimple, BalanceUtxo

balance = client.blockchain.data.get_balance("BTC", "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")

# The balance shape depends on the chain. The SDK returns the matching model:
if isinstance(balance, BalanceUtxo):  # BTC, LTC, DOGE
    print(balance.balance, balance.incomingPending)
elif isinstance(balance, BalanceSimple):  # ETH, SOL, BNB, MATIC, ...
    print(balance.balance)

rate = client.blockchain.data.get_exchange_rate("BTC", base_pair="USD")
print(rate.value)

fees = client.blockchain.fee.get_recommended_fee("BTC")
print(fees.slow, fees.medium, fees.fast)
```

Several blockchain operations return a different shape per chain (for example `get_balance`, `get_transaction_history`, `lookups.get_transaction`, `lookups.get_block`, and `wallet.generate`). Each is typed as a `Union` of the documented shapes, and the SDK picks the right model, so you can branch with `isinstance`.

### Cards

```python
card = client.card.cards.create(
    product_code="us_493_visa_bin",  # see client.card.cards.list_products()
    first_name="Jane",
    last_name="Doe",
    email="jane@example.com",
    initial_load=20,
    tags=["Marketing"],
)
print(card.data.card_id, card.data.status)

client.card.cards.fund(card.data.card_id, 50)

for row in client.card.balance.list_all_transactions():
    print(row.created_at, row.type, row.amount_usd)
```

### Compliance

```python
presets = client.compliance.presets.list()

session = client.compliance.sessions.create(
    preset_id=presets.presets[0].id,
    external_user_id="user_42",  # your own identifier for the end user
)
print("Send the user to:", session.url)

# Later: read the result (or receive it via your registered webhook).
result = client.compliance.sessions.get(session.session_id)
print(result.status, [r.feature for r in result.results])

# Iterate over every session; pages are fetched lazily.
for s in client.compliance.sessions.list_all(status="In Review"):
    print(s.session_id, s.external_user_id)

screening = client.compliance.wallet_screening.create(
    address="0x0000000000000000000000000000000000000000",
    chain="ETH",
    idempotency_key="screen-0x0000-2026-10-01",
)
print(screening.result.severity, screening.result.sanctions_hit)
```

Captured documents and report PDFs are binary. Those methods return a `BinaryResponse`:

```python
photo = client.compliance.sessions.get_document(session.session_id, "portrait_image")
photo.write_to("portrait.jpg")
print(photo.content_type)  # "image/jpeg"
```

## Error handling

Any non-2xx response raises `CrypturesApiError`, or one of its status-specific subclasses. Every error carries the fields of the API's error envelope:

```python
from cryptures import (
    Cryptures,
    CrypturesApiError,
    CrypturesConnectionError,
    InsufficientBalanceError,
    PermissionDeniedError,
)

try:
    client.card.cards.fund("card_a1b2c3d4", 100)
except InsufficientBalanceError as err:
    print("Top up your balance first:", err.message)
except PermissionDeniedError as err:
    print(err.code)  # e.g. "forbidden_card" or "forbidden_scope"
except CrypturesApiError as err:
    print(err.status_code, err.code, err.message)
    print("Quote this to support:", err.request_id)
except CrypturesConnectionError:
    print("Network problem; the request could not be completed.")
```

| Exception | When |
| --- | --- |
| `BadRequestError` | 400, e.g. `invalid_request` |
| `AuthenticationError` | 401, missing or invalid API key |
| `InsufficientBalanceError` | 402, `insufficient_balance` |
| `PermissionDeniedError` | 403, e.g. `forbidden_scope`, `forbidden_card` |
| `NotFoundError` | 404 |
| `ConflictError` | 409, e.g. `tag_name_taken`, `idempotency_key_reused` |
| `GoneError` | 410, e.g. `report_expired` |
| `RateLimitError` | 429, `rate_limited` |
| `InternalServerError` | 5xx |
| `CrypturesApiError` | base class for all of the above |
| `CrypturesConnectionError` / `CrypturesTimeoutError` | the request did not complete at the network level |
| `CrypturesResponseValidationError` | a 2xx body did not match the documented shape (the raw body is on `.body`) |

All of these derive from `CrypturesError`.

Some operations are documented to return a different error body. Card operations can forward the card issuer's own `{status, message, code}` body, and `exchange.rate` uses a rate-not-found body. The SDK maps these onto the same `code` and `message` attributes, and the original body is always available as `err.body`.

## Retries and idempotency

The client retries automatically, with exponential backoff (about 0.25s, 0.5s, then 1s, with jitter), up to `max_retries` times (default 3):

- **4xx responses are never retried.**
- **Failures to connect** (DNS, connection refused, connect timeout) are retried for every call, because the request never reached the API.
- **5xx responses and other network errors** (read timeouts, dropped connections) are retried only for calls that are safe to repeat: reads, writes the API documents as idempotent, and calls sent with an idempotency key.
- **Calls that are not safe to repeat are not re-sent** once the request may have reached the API. These are `operations.send_transaction`, `operations.broadcast`, `operations.rpc`, `contracts.*`, `cards.create`/`fund`/`withdraw`, `tags.create`, `sessions.create`, `storage.upload_to_ipfs`, and `wallet.generate`, where a retry would return a different new wallet. For calls that move money or broadcast a transaction, the API documents that a 5xx does **not** mean nothing happened. Check the outcome, for example with `get_transaction_history` or `card.balance.list_transactions`, before you retry yourself.

`compliance.aml.check` and `compliance.wallet_screening.create` support the API's `Idempotency-Key` header. Pass `idempotency_key=...` and a repeated call with the same key returns the original result without screening or charging again. With a key, the SDK also retries those calls automatically.

```python
client = Cryptures(api_key="...", timeout=10.0, max_retries=5)
```

## Configuration

```python
import httpx
from cryptures import Cryptures

client = Cryptures(
    api_key="...",
    base_url="https://api.cryptures.com",  # default
    timeout=30.0,  # seconds, or an httpx.Timeout
    max_retries=3,
    default_headers={"X-My-Trace-Id": "abc"},
    http_client=httpx.Client(proxy="http://proxy.internal:8080"),  # optional; you manage its lifecycle
)
```

## Models

Responses are [Pydantic v2](https://docs.pydantic.dev/) models from `cryptures.types`. Field names match the API's wire format exactly (`txId`, `balance_usd`, `nextPage`), so what you read in the [API reference](https://docs.cryptures.com/) is what you access in Python. The only exceptions are names that are not valid Python identifiers. `from` becomes `from_`, and the exchange-detail object keyed `"0"` becomes `metadata`.

Fields the API adds later are kept, not dropped. You can read them as attributes or through `model.model_extra`. Call `model.to_dict()` to get the wire-format dict back.

## Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

pytest            # tests
mypy              # strict type checking
ruff check .      # lint
ruff format .     # format
```

The test suite has a declarative case for every API operation (`tests/cases_*.py`), and `tests/test_coverage.py` fails if any documented operation or public SDK method is left without one.

## Contributing

Issues and pull requests are welcome at [github.com/Cryptures-com/cryptures-sdk-python](https://github.com/Cryptures-com/cryptures-sdk-python/issues). Before you open a PR, make sure `pytest`, `mypy`, and `ruff check .` all pass. If your change touches an endpoint, check it against the [API reference](https://docs.cryptures.com/). Every endpoint, parameter, and field in this SDK comes from the documented API.

For questions about your account or the API itself, see [cryptures.com](https://cryptures.com).

## License

[MIT](LICENSE)
