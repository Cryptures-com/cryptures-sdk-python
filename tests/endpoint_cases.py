"""Every endpoint test case, across all domains.

Each case states exactly what the SDK must send (HTTP method, path, query,
JSON body, extra headers) and a response body taken from the API reference's
own examples, plus a check that the parsed result has the right type and
values. ``test_endpoints.py`` runs every case; ``test_coverage.py`` proves
every public SDK method and every documented operation id has a case.
"""

from __future__ import annotations

from typing import List

from ._case import Case
from .cases_blockchain import BLOCKCHAIN_CASES
from .cases_card import CARD_CASES

__all__ = ["CASES", "Case"]

CASES: List[Case] = [*BLOCKCHAIN_CASES, *CARD_CASES]
