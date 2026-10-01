"""Models for the ``card`` domain (shown as "Expense Management" in the API reference)."""

from __future__ import annotations

from typing import List, Optional

from pydantic import Field

from .._models import CrypturesModel, Number

__all__ = [
    "BalanceTransaction",
    "BalanceTransactionList",
    "Card",
    "CardAmountData",
    "CardBalance",
    "CardBalanceAmount",
    "CardFundResponse",
    "CardList",
    "CardListItem",
    "CardProduct",
    "CardProductList",
    "CardResponse",
    "CardSetPinResponse",
    "CardStatusChangeResponse",
    "CardStatusData",
    "CardTag",
    "CardTags",
    "CardTransaction",
    "CardTransactionsData",
    "CardTransactionsPagination",
    "CardTransactionsResponse",
    "CardWithdrawResponse",
    "ReportByCard",
    "ReportByMonth",
    "ReportByTag",
    "ReportByType",
    "ReportCardTag",
    "ReportRange",
    "ReportSummary",
    "ReportTotals",
    "ReportUnattributed",
    "ReportUntagged",
    "Tag",
    "TagDeleted",
    "TagList",
    "TagUpdated",
]


class CardTag(CrypturesModel):
    """A tag attached to a card."""

    tag_id: str
    name: str
    color: str
    """Hex color, e.g. ``"#4F46E5"``."""


class CardBalanceAmount(CrypturesModel):
    """A card's own balance (distinct from the project-level balance)."""

    amount: int
    """Balance in micro-units (divide by 1,000,000 for a display value)."""
    display_amount: Number
    currency: str


class Card(CrypturesModel):
    """A virtual card.

    ``card_number``, ``cardnumber`` (same PAN, second key) and ``cvv`` are
    present for API-key callers; ``email`` here is a system-generated
    placeholder -- use ``card.cards.list()`` for the real cardholder email.
    """

    card_id: str
    product_code: Optional[str] = None
    brand: Optional[str] = None
    type: Optional[str] = None
    currency: Optional[str] = None
    status: str
    """e.g. ``"active"``, ``"blocked"``, ``"terminated"``."""
    name_on_card: Optional[str] = None
    email: Optional[str] = None
    last_four: Optional[str] = None
    expiry_month: Optional[str] = None
    expiry_year: Optional[str] = None
    balance: Optional[CardBalanceAmount] = None
    card_number: Optional[str] = None
    cvv: Optional[str] = None
    cardnumber: Optional[str] = None
    expiredate: Optional[str] = None
    """Expiry pre-combined as ``"MM/YY"``."""
    created_at: Optional[str] = None
    tags: Optional[List[CardTag]] = None


class CardResponse(CrypturesModel):
    """Envelope returned by card.create and card.get."""

    status: str
    message: Optional[str] = None
    data: Card


class CardSetPinResponse(CrypturesModel):
    status: str
    message: Optional[str] = None


class CardAmountData(CrypturesModel):
    card_id: str
    amount: int
    """Confirmed amount in micro-units (divide by 1,000,000 for USD)."""
    display_amount: Number


class CardFundResponse(CrypturesModel):
    status: str
    data: CardAmountData


class CardWithdrawResponse(CrypturesModel):
    status: str
    message: Optional[str] = None
    data: CardAmountData


class CardStatusData(CrypturesModel):
    card_id: str
    status: str


class CardStatusChangeResponse(CrypturesModel):
    """Envelope returned by card.terminate, card.block and card.unblock."""

    status: str
    message: Optional[str] = None
    data: Optional[CardStatusData] = None


class CardTransaction(CrypturesModel):
    """One card transaction.

    The API reference marks this response as provisional (it is the card
    issuer's own body, forwarded verbatim), so every field here is optional
    and unknown fields are kept.
    """

    id: Optional[str] = None
    card_id: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None
    amount: Optional[int] = None
    """Amount in micro-units (divide by 1,000,000 for USD)."""
    display_amount: Optional[Number] = None
    currency: Optional[str] = None
    merchant_name: Optional[str] = None
    created_at: Optional[str] = None


class CardTransactionsPagination(CrypturesModel):
    type: Optional[str] = None
    page_num: Optional[int] = None
    page_size: Optional[int] = None
    total: Optional[int] = None
    has_more: Optional[bool] = None


class CardTransactionsData(CrypturesModel):
    transactions: Optional[List[CardTransaction]] = None
    pagination: Optional[CardTransactionsPagination] = None


class CardTransactionsResponse(CrypturesModel):
    status: Optional[str] = None
    message: Optional[str] = None
    data: Optional[CardTransactionsData] = None


class CardListItem(CrypturesModel):
    card_id: str
    product_code: str
    email: str
    """The real cardholder email supplied at creation time."""
    first_name: str
    last_name: str
    status: str
    last_four: Optional[str] = None
    """``None`` if never populated -- always null-check this field."""
    label: Optional[str] = None
    """Reserved for future use -- always ``None`` today."""
    created_at: str
    tags: List[CardTag]


class CardList(CrypturesModel):
    data: List[CardListItem]


class CardProduct(CrypturesModel):
    product_code: str
    display_name: str
    min_load_usd: Optional[Number]
    max_load_usd: Optional[Number]
    issuance_fee_usd: Number
    fund_fee_flat_usd: Number
    fund_fee_pct: Number
    """Percentage fee (0-1) applied to every funding amount."""
    annual_fee_usd: Optional[Number]
    disallow_initial_load: bool
    """When true, create cards of this product without ``initial_load``."""


class CardProductList(CrypturesModel):
    products: List[CardProduct]


class CardBalance(CrypturesModel):
    """The project's shared USD balance used by card operations."""

    balance_usd: Number
    updated_at: Optional[str]


class BalanceTransaction(CrypturesModel):
    """One row of the project's whole-account balance ledger."""

    id: str
    type: str
    """e.g. ``card_fund_debit``. New types can appear -- handle unknown values gracefully."""
    amount_usd: Number
    related_reference: Optional[str]
    """What this points at depends on ``type`` (a card_id, check id, session id, ...)."""
    status: str
    """One of ``pending``, ``completed``, ``reversed``, ``disputed``."""
    created_at: str


class BalanceTransactionList(CrypturesModel):
    data: List[BalanceTransaction]
    page: int
    limit: int
    total: int
    """Total row count across all pages."""


class Tag(CrypturesModel):
    tag_id: str
    name: str
    color: str
    created_at: str
    updated_at: str


class TagList(CrypturesModel):
    data: List[Tag]


class TagUpdated(CrypturesModel):
    tag_id: str
    name: str
    color: str
    updated_at: str


class TagDeleted(CrypturesModel):
    deleted: bool


class CardTags(CrypturesModel):
    """A card's tags after a replace (card.tags.set)."""

    tags: List[CardTag]


class ReportRange(CrypturesModel):
    from_: str = Field(alias="from")
    to: str


class ReportTotals(CrypturesModel):
    funded_usd: Number
    withdrawn_usd: Number
    net_usd: Number
    card_count: int
    """Distinct card references on matching ledger rows -- counted differently from other ``card_count``s."""


class ReportUnattributed(CrypturesModel):
    funded_usd: Number


class ReportByMonth(CrypturesModel):
    month: Optional[str] = None
    """``YYYY-MM``."""
    funded_usd: Optional[Number] = None
    withdrawn_usd: Optional[Number] = None
    net_usd: Optional[Number] = None


class ReportByType(CrypturesModel):
    product_code: Optional[str] = None
    funded_usd: Optional[Number] = None
    withdrawn_usd: Optional[Number] = None
    net_usd: Optional[Number] = None
    card_count: Optional[int] = None


class ReportByTag(CrypturesModel):
    tag_id: Optional[str] = None
    name: Optional[str] = None
    color: Optional[str] = None
    funded_usd: Optional[Number] = None
    withdrawn_usd: Optional[Number] = None
    net_usd: Optional[Number] = None
    card_count: Optional[int] = None


class ReportUntagged(CrypturesModel):
    funded_usd: Number
    withdrawn_usd: Number
    net_usd: Number
    card_count: int


class ReportCardTag(CrypturesModel):
    tag_id: Optional[str] = None
    name: Optional[str] = None
    color: Optional[str] = None


class ReportByCard(CrypturesModel):
    card_id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    last_four: Optional[str] = None
    product_code: Optional[str] = None
    tags: Optional[List[ReportCardTag]] = None
    funded_usd: Optional[Number] = None
    withdrawn_usd: Optional[Number] = None
    net_usd: Optional[Number] = None


class ReportSummary(CrypturesModel):
    """Card funding/withdrawal report (card.reports.summary)."""

    range: ReportRange
    totals: ReportTotals
    unattributed: ReportUnattributed
    by_month: List[ReportByMonth]
    by_type: List[ReportByType]
    by_tag: List[ReportByTag]
    untagged: ReportUntagged
    by_card: List[ReportByCard]
