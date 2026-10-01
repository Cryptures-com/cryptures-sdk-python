from __future__ import annotations

from typing import Literal, Optional

from ..._http import ResponseParser, build_path
from ...types.compliance import AmlCheck, WalletScreening
from .._base import APIResource, drop_none, idempotency_headers

__all__ = ["ComplianceAml", "ComplianceWalletScreening"]

_AML: ResponseParser[AmlCheck] = ResponseParser(AmlCheck)
_WALLET_SCREENING: ResponseParser[WalletScreening] = ResponseParser(WalletScreening)


class ComplianceAml(APIResource):
    """Standalone AML (sanctions, PEP, adverse media) screening."""

    def check(
        self,
        *,
        external_user_id: str,
        full_name: str,
        date_of_birth: Optional[str] = None,
        nationality: Optional[str] = None,
        entity_type: Optional[Literal["person", "company"]] = None,
        idempotency_key: Optional[str] = None,
    ) -> AmlCheck:
        """Screen a person or company against AML lists (``compliance.aml.check``).

        Billed per successful call. Pass ``idempotency_key`` (1-128 printable
        characters, sent as ``Idempotency-Key``) to make retries safe: a
        repeat with the same key and request returns the original result
        without screening or charging again. With a key, this SDK also
        retries transient failures automatically; without one, it does not
        re-send a request that may have reached the API.

        Args:
            external_user_id: Your own identifier for the subject.
            full_name: Person or company name (max 200 characters).
            date_of_birth: ``YYYY-MM-DD``; improves matching for people.
            nationality: ISO 3166-1 alpha-2 code, e.g. ``"ES"``.
            entity_type: ``"person"`` (default) or ``"company"``.
            idempotency_key: Optional ``Idempotency-Key`` header value.
        """
        body = drop_none(
            external_user_id=external_user_id,
            full_name=full_name,
            date_of_birth=date_of_birth,
            nationality=nationality,
            entity_type=entity_type,
        )
        return self._http.request_json(
            "POST",
            "/api/v1/compliance/aml/checks",
            parser=_AML,
            retry_safe=idempotency_key is not None,
            json=body,
            headers=idempotency_headers(idempotency_key),
        )


class ComplianceWalletScreening(APIResource):
    """Blockchain-address risk screening."""

    def create(self, *, address: str, chain: str, idempotency_key: Optional[str] = None) -> WalletScreening:
        """Screen a public blockchain address for risk exposure (``compliance.wallet_screening.create``).

        Billed per successful call; ``idempotency_key`` behaves as on
        ``compliance.aml.check``.

        Args:
            address: The address (1-128 characters).
            chain: One of ``BTC``, ``ETH``, ``BNB``, ``MATIC``, ``TRON`` (or
                ``TRX``), ``LTC``, ``DOGE``, ``SOL``, ``XRP``, ``BCH``
                (case-insensitive).
            idempotency_key: Optional ``Idempotency-Key`` header value.
        """
        return self._http.request_json(
            "POST",
            "/api/v1/compliance/wallet-screenings",
            parser=_WALLET_SCREENING,
            retry_safe=idempotency_key is not None,
            json={"address": address, "chain": chain},
            headers=idempotency_headers(idempotency_key),
        )

    def get(self, check_id: str) -> WalletScreening:
        """Read back a stored wallet screening, free of charge (``compliance.wallet_screening.get``)."""
        path = build_path("/api/v1/compliance/wallet-screenings/{check_id}", check_id=check_id)
        return self._http.request_json("GET", path, parser=_WALLET_SCREENING, retry_safe=True)
