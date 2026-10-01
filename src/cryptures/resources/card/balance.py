from __future__ import annotations

from typing import Iterator, Optional

from ..._http import ResponseParser
from ...types.card import BalanceTransaction, BalanceTransactionList, CardBalance
from .._base import APIResource

__all__ = ["CardBalanceResource"]

_BALANCE: ResponseParser[CardBalance] = ResponseParser(CardBalance)
_TRANSACTIONS: ResponseParser[BalanceTransactionList] = ResponseParser(BalanceTransactionList)


class CardBalanceResource(APIResource):
    """The project's shared USD balance and its ledger."""

    def get(self) -> CardBalance:
        """Get the project's shared USD balance (``card.balance.get``)."""
        return self._http.request_json("GET", "/api/v1/card/balance", parser=_BALANCE, retry_safe=True)

    def list_transactions(
        self, *, page: Optional[int] = None, limit: Optional[int] = None
    ) -> BalanceTransactionList:
        """List one page of the project's balance ledger, newest first (``card.balance.transactions``).

        This is the whole-account ledger (card debits/credits, deposits, plan
        charges, compliance charges, ...); branch on each row's ``type``.

        Args:
            page: 1-indexed page number (default 1).
            limit: Rows per page (default 50, clamped to 200 server-side).
        """
        return self._http.request_json(
            "GET",
            "/api/v1/card/balance/transactions",
            parser=_TRANSACTIONS,
            retry_safe=True,
            params={"page": page, "limit": limit},
        )

    def list_all_transactions(self, *, limit: Optional[int] = None) -> Iterator[BalanceTransaction]:
        """Iterate over every ledger row, newest first, fetching pages lazily."""
        page = 1
        seen = 0
        while True:
            result = self.list_transactions(page=page, limit=limit)
            yield from result.data
            seen += len(result.data)
            if not result.data or seen >= result.total:
                return
            page += 1
