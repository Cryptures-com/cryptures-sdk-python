from __future__ import annotations

from ..._http import HttpClient
from .balance import CardBalanceResource
from .cards import CardCards
from .reports import CardReports
from .tags import CardTagsResource
from .webhooks import CardWebhooks

__all__ = ["Card", "CardBalanceResource", "CardCards", "CardReports", "CardTagsResource", "CardWebhooks"]


class Card:
    """The ``card`` domain (shown as "Expense Management" in the API reference)."""

    def __init__(self, http: HttpClient) -> None:
        self.cards = CardCards(http)
        self.balance = CardBalanceResource(http)
        self.tags = CardTagsResource(http)
        self.reports = CardReports(http)
        self.webhooks = CardWebhooks(http)
