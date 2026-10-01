from __future__ import annotations

import datetime as _dt
from typing import Optional, Union

from ..._http import ResponseParser
from ...types.card import ReportSummary
from .._base import APIResource

__all__ = ["CardReports"]

_SUMMARY: ResponseParser[ReportSummary] = ResponseParser(ReportSummary)

DateLike = Union[str, _dt.datetime, _dt.date]


def _iso(value: Optional[DateLike]) -> Optional[str]:
    if value is None or isinstance(value, str):
        return value
    return value.isoformat()


class CardReports(APIResource):
    """Card funding and withdrawal reports."""

    def summary(self, *, from_: Optional[DateLike] = None, to: Optional[DateLike] = None) -> ReportSummary:
        """Summarize card funding/withdrawals over a date range (``card.reports.summary``).

        Defaults to the trailing 12 months. Only ``completed`` ledger rows count.

        Args:
            from_: Start of the range (inclusive), ISO 8601 string or datetime/date (sent as ``from``).
            to: End of the range (exclusive), ISO 8601 string or datetime/date.
        """
        return self._http.request_json(
            "GET",
            "/api/v1/card/reports/summary",
            parser=_SUMMARY,
            retry_safe=True,
            params={"from": _iso(from_), "to": _iso(to)},
        )
