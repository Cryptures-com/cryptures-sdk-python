# Changelog

## 0.1.1 (2026-10-02)

### Security

- **`CrypturesConnectionError` no longer exposes the request.** It used to keep the raw `httpx.Request` as `err.request`, which exposed two things. The request URL could contain a secret, such as an EGLD mnemonic passed to `wallet.derive_address` in the path, or a `mnemonic` query parameter. The `x-api-key` header held the full, unredacted API key; httpx redacts only `Authorization`. Error trackers and debuggers that serialize exception attributes could record both. The `request` attribute has been removed. The exception now carries `method` and `path_template` (for example `"/api/v1/blockchain/wallet/{chain}"`) as plain strings. Its message names the call by that template, not the filled-in path. The httpx cause is kept as `__cause__` with the same type and message, minus its `request`. Any URL or API key in that message is replaced with `[REDACTED]`.
- `CrypturesApiError.message`, `code` and `request_id` now have CR, LF and other control characters replaced with spaces, and each is capped at 1024 characters. This stops a malicious or buggy upstream from injecting forged log lines. The decoded body is still in `err.body`.
- At most 1 MiB of an error response body is read, matching the Go SDK. A misbehaving intermediary can no longer exhaust memory.

### Changed

- **Retry behavior is now identical across the Python, JavaScript and Go SDKs.** `card.cards.set_pin`, `block`, `unblock` and `terminate` are no longer retried automatically after a 5xx or a dropped connection. These state changes are forwarded to the card issuer. Failures to *connect* are still retried for every call, because those requests never reached the API.
- Error messages for unexpected response bodies name the call by its path template, not the filled-in path.

### Breaking (security)

- `CrypturesConnectionError.request` was removed; use `err.method` and `err.path_template`. `CrypturesTimeoutError` is a subclass and changed the same way.
