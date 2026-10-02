from __future__ import annotations

from typing import Optional, Sequence, Union

from ..._http import ResponseParser, build_path
from ..._models import Number
from ...types.card import (
    CardFundResponse,
    CardList,
    CardProductList,
    CardResponse,
    CardSetPinResponse,
    CardStatusChangeResponse,
    CardTags,
    CardTransactionsResponse,
    CardWithdrawResponse,
)
from .._base import APIResource, drop_none

__all__ = ["CardCards"]

_CARD: ResponseParser[CardResponse] = ResponseParser(CardResponse)
_CARD_LIST: ResponseParser[CardList] = ResponseParser(CardList)
_SET_PIN: ResponseParser[CardSetPinResponse] = ResponseParser(CardSetPinResponse)
_FUND: ResponseParser[CardFundResponse] = ResponseParser(CardFundResponse)
_WITHDRAW: ResponseParser[CardWithdrawResponse] = ResponseParser(CardWithdrawResponse)
_STATUS_CHANGE: ResponseParser[CardStatusChangeResponse] = ResponseParser(CardStatusChangeResponse)
_TRANSACTIONS: ResponseParser[CardTransactionsResponse] = ResponseParser(CardTransactionsResponse)
_CARD_TAGS: ResponseParser[CardTags] = ResponseParser(CardTags)
_PRODUCTS: ResponseParser[CardProductList] = ResponseParser(CardProductList)


class CardCards(APIResource):
    """Virtual cards: issue, fund, withdraw, freeze, terminate, PIN, tags, transactions.

    Once a request passes Cryptures' own checks, the card issuer's answer is
    forwarded verbatim -- including failures, which then carry the issuer's
    ``{"status": "failure", "message", "code"}`` body. Those still raise
    :class:`~cryptures.CrypturesApiError`, with ``code``/``message`` taken
    from that body.

    Money-moving calls (:meth:`create`, :meth:`fund`, :meth:`withdraw`) are
    never retried after the request may have reached the API.
    """

    def create(
        self,
        *,
        product_code: str,
        first_name: str,
        last_name: str,
        email: str,
        initial_load: Optional[Number] = None,
        tags: Optional[Sequence[str]] = None,
    ) -> CardResponse:
        """Create a virtual card (``card.create``).

        Atomically debits the project's shared USD balance for
        ``initial_load`` + issuance fee + top-up fee + annual fee; raises
        :class:`~cryptures.InsufficientBalanceError` (402) if it cannot.

        Args:
            product_code: A product code from :meth:`list_products`.
            first_name: Cardholder first name.
            last_name: Cardholder last name.
            email: The real cardholder email (returned later by :meth:`list`).
            initial_load: USD to load. Required for every product except those
                whose ``disallow_initial_load`` is true (e.g.
                ``us_493_visa_atm``), which must omit it.
            tags: Up to 10 tag names (1-50 chars each) to attach.
        """
        body = drop_none(
            product_code=product_code,
            first_name=first_name,
            last_name=last_name,
            email=email,
            initial_load=initial_load,
            tags=list(tags) if tags is not None else None,
        )
        return self._http.request_json(
            "POST", "/api/v1/card/cards/create", parser=_CARD, retry_safe=False, json=body
        )

    def get(self, card_id: str, *, reveal_token: Optional[str] = None) -> CardResponse:
        """Fetch a card by id (``card.get``).

        ``reveal_token`` only matters for dashboard-session callers; API-key
        callers always receive the unmasked card.
        """
        path = build_path("/api/v1/card/cards/{card_id}", card_id=card_id)
        return self._http.request_json(
            "GET", path, parser=_CARD, retry_safe=True, params={"reveal_token": reveal_token}
        )

    def list(self) -> CardList:
        """List every card belonging to the project, newest first (``card.list``)."""
        return self._http.request_json("GET", "/api/v1/card/cards", parser=_CARD_LIST, retry_safe=True)

    def set_pin(self, card_id: str, pin: str) -> CardSetPinResponse:
        """Set a 6-digit PIN (``card.setpin``). Only for ``us_493_visa_atm`` cards."""
        path = build_path("/api/v1/card/cards/{card_id}/pin", card_id=card_id)
        # Card state changes are forwarded to the card issuer and are not
        # retried automatically (same policy in the Go and JS SDKs).
        return self._http.request_json("POST", path, parser=_SET_PIN, retry_safe=False, json={"pin": pin})

    def fund(self, card_id: str, amount: Number) -> CardFundResponse:
        """Add USD funds to a card (``card.fund``).

        Debits ``amount`` plus the product's top-up fee from the project
        balance; raises :class:`~cryptures.InsufficientBalanceError` (402) if
        it cannot be covered.
        """
        path = build_path("/api/v1/card/cards/{card_id}/fund", card_id=card_id)
        return self._http.request_json("POST", path, parser=_FUND, retry_safe=False, json={"amount": amount})

    def withdraw(self, card_id: str, amount: Number) -> CardWithdrawResponse:
        """Withdraw USD from a card back to the project balance (``card.withdraw``)."""
        path = build_path("/api/v1/card/cards/{card_id}/withdraw", card_id=card_id)
        return self._http.request_json(
            "POST", path, parser=_WITHDRAW, retry_safe=False, json={"amount": amount}
        )

    def terminate(self, card_id: str) -> CardStatusChangeResponse:
        """Permanently terminate a card (``card.terminate``)."""
        path = build_path("/api/v1/card/cards/{card_id}/terminate", card_id=card_id)
        return self._http.request_json("POST", path, parser=_STATUS_CHANGE, retry_safe=False)

    def block(self, card_id: str) -> CardStatusChangeResponse:
        """Freeze a card (``card.block``)."""
        path = build_path("/api/v1/card/cards/{card_id}/block", card_id=card_id)
        return self._http.request_json("POST", path, parser=_STATUS_CHANGE, retry_safe=False)

    def unblock(self, card_id: str) -> CardStatusChangeResponse:
        """Unfreeze a previously blocked card (``card.unblock``)."""
        path = build_path("/api/v1/card/cards/{card_id}/unblock", card_id=card_id)
        return self._http.request_json("POST", path, parser=_STATUS_CHANGE, retry_safe=False)

    def list_transactions(
        self, card_id: str, *, page_num: Optional[Union[int, str]] = None
    ) -> CardTransactionsResponse:
        """Get a card's transaction history (``card.transactions``).

        ``page_num`` (sent as ``pageNum``) is the only pagination parameter and
        is forwarded to the issuer unvalidated. The API reference marks this
        response shape as provisional, so every field is optional.
        """
        path = build_path("/api/v1/card/cards/{card_id}/transactions", card_id=card_id)
        params = {"pageNum": str(page_num) if page_num is not None else None}
        return self._http.request_json("GET", path, parser=_TRANSACTIONS, retry_safe=True, params=params)

    def set_tags(self, card_id: str, tags: Sequence[str]) -> CardTags:
        """Replace a card's entire tag list (``card.tags.set``).

        This is a full replace: ``[]`` removes every tag. Names are trimmed and
        de-duplicated case-insensitively, so the returned list can be shorter
        than what you sent. At most 10 names, 1-50 characters each.
        """
        if isinstance(tags, str):
            raise TypeError("tags must be a sequence of tag names, not a single string")
        path = build_path("/api/v1/card/cards/{card_id}/tags", card_id=card_id)
        return self._http.request_json(
            "PUT", path, parser=_CARD_TAGS, retry_safe=True, json={"tags": list(tags)}
        )

    def list_products(self) -> CardProductList:
        """List the card products currently available for issuance (``card.products.list``)."""
        return self._http.request_json("GET", "/api/v1/card/products", parser=_PRODUCTS, retry_safe=True)
