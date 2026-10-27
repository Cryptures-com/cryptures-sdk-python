from __future__ import annotations

from typing import Optional, Sequence, Tuple, Union

from ..._http import FileTuple, ResponseParser, build_path
from ..._models import Number
from ...types.card import (
    CardFundResponse,
    CardKycSubmitResponse,
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
from .._files import FileInput, read_file

__all__ = ["CardCards", "KycDocument"]

#: A KYC document: a file (bytes, path, or binary file object), optionally as a
#: ``(filename, file)`` or ``(filename, file, content_type)`` tuple.
KycDocument = Union[FileInput, Tuple[str, FileInput], Tuple[str, FileInput, str]]

_CARD: ResponseParser[CardResponse] = ResponseParser(CardResponse)
_CARD_LIST: ResponseParser[CardList] = ResponseParser(CardList)
_SET_PIN: ResponseParser[CardSetPinResponse] = ResponseParser(CardSetPinResponse)
_FUND: ResponseParser[CardFundResponse] = ResponseParser(CardFundResponse)
_WITHDRAW: ResponseParser[CardWithdrawResponse] = ResponseParser(CardWithdrawResponse)
_STATUS_CHANGE: ResponseParser[CardStatusChangeResponse] = ResponseParser(CardStatusChangeResponse)
_TRANSACTIONS: ResponseParser[CardTransactionsResponse] = ResponseParser(CardTransactionsResponse)
_CARD_TAGS: ResponseParser[CardTags] = ResponseParser(CardTags)
_PRODUCTS: ResponseParser[CardProductList] = ResponseParser(CardProductList)
_KYC_SUBMIT: ResponseParser[CardKycSubmitResponse] = ResponseParser(CardKycSubmitResponse)


class CardCards(APIResource):
    """Virtual cards: issue, fund, withdraw, freeze, terminate, PIN, tags, transactions.

    Once a request passes Cryptures' own checks, the card issuer's answer is
    forwarded verbatim -- including failures, which then carry the issuer's
    ``{"status": "failure", "message", "code"}`` body. Those still raise
    :class:`~cryptures.CrypturesApiError`, with ``code``/``message`` taken
    from that body.

    Money-moving and charged calls (:meth:`create`, :meth:`fund`,
    :meth:`withdraw`, :meth:`submit_kyc`) are never retried after the request
    may have reached the API.
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

    def submit_kyc(
        self,
        card_id: str,
        *,
        document_front: KycDocument,
        document_back: Optional[KycDocument] = None,
    ) -> CardKycSubmitResponse:
        """Submit the cardholder's identity documents for a card (``card.kyc.submit``).

        Sent as ``multipart/form-data`` with a ``documentFront`` file field
        and, if given, a ``documentBack`` field. Each file must be a PNG,
        JPG/JPEG or PDF of at most 2 MB; the API checks the type from the
        file's content and returns the validation error, so nothing is
        pre-validated here. Documents are forwarded to the card issuer and
        never stored by Cryptures. Check ``card.kyc.supported`` (card
        get/list) or ``kyc_supported`` (:meth:`list_products`) first.

        A one-time KYC fee (``kyc_fee_usd`` on :meth:`list_products`) is
        charged per card from the project's shared USD balance before the
        documents are submitted. The fee is set per product and can be 0: then
        ``fee_charged_usd`` is 0 and the upload is free. Submitting again for
        the same card is not charged again (``fee_already_paid``). On success
        a ``card.kyc_submitted`` webhook event fires, if a card webhook is
        registered.

        This call is charged and not idempotent, so it is never retried
        automatically after the request may have reached the API (only a
        failure to connect is retried). On 502 or 504 the outcome is unknown
        and the fee is held for review: check ``kyc.submitted`` on :meth:`get`
        and the balance ledger before submitting again.

        Args:
            card_id: The card to submit documents for.
            document_front: Front of the identity document (required). Raw
                bytes, a filesystem path (``str`` or ``PathLike``), a binary
                file object, or a ``(filename, file)`` /
                ``(filename, file, content_type)`` tuple, where ``file`` is
                any of the former. The filename defaults to the path's
                basename (the field name for raw bytes, ``"upload"`` for unnamed file objects) and the content
                type is detected from the content (PNG, JPEG, PDF).
            document_back: Back of the document (optional); same forms.

        Raises:
            ~cryptures.BadRequestError: 400 ``invalid_request`` (not valid
                multipart), ``missing_document_front``, ``too_many_files``,
                ``invalid_file_type``, or ``kyc_rejected`` (the issuer refused
                the documents; the fee is refunded automatically).
            ~cryptures.InsufficientBalanceError: 402 ``insufficient_balance``;
                nothing is charged or submitted.
            ~cryptures.NotFoundError: 404 ``card_not_found``.
            ~cryptures.ConflictError: 409 ``kyc_not_supported`` (the product
                does not accept KYC), ``kyc_email_unknown`` (the card was not
                issued through this service; contact support) or
                ``kyc_in_progress`` (a submission is already being processed).
            ~cryptures.CrypturesApiError: 413 ``file_too_large`` (over 2 MB)
                or ``payload_too_large``.
            ~cryptures.RateLimitError: 429 ``rate_limited`` (5 submissions per
                card per day, plus a per-minute limit); honour ``Retry-After``.
            ~cryptures.InternalServerError: 502 ``upstream_error`` or 504
                ``upstream_timeout``; the outcome is unknown (see above).
        """
        path = build_path("/api/v1/card/cards/{card_id}/kyc", card_id=card_id)
        files = {"documentFront": _kyc_file("documentFront", document_front)}
        if document_back is not None:
            files["documentBack"] = _kyc_file("documentBack", document_back)
        return self._http.request_json("POST", path, parser=_KYC_SUBMIT, retry_safe=False, files=files)

    def list_products(self) -> CardProductList:
        """List the card products currently available for issuance (``card.products.list``)."""
        return self._http.request_json("GET", "/api/v1/card/products", parser=_PRODUCTS, retry_safe=True)


def _detect_content_type(data: bytes) -> str:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"%PDF-"):
        return "application/pdf"
    return "application/octet-stream"


def _kyc_file(field: str, document: KycDocument) -> FileTuple:
    """Turn a :data:`KycDocument` into the ``(filename, bytes, content_type)`` part httpx expects."""
    filename: Optional[str] = None
    content_type: Optional[str] = None
    source: FileInput
    if isinstance(document, tuple):
        if len(document) == 2:
            filename, source = document
        elif len(document) == 3:
            filename, source, content_type = document
        else:
            raise TypeError(f"{field} tuples must be (filename, file) or (filename, file, content_type)")
    else:
        source = document
    name, data = read_file(source, filename)
    if filename is None and isinstance(source, bytes):
        name = field
    return name, data, content_type or _detect_content_type(data)
