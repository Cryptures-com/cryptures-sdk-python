"""Proves the endpoint table covers every documented operation and every public SDK method."""

from __future__ import annotations

import inspect
from collections import Counter
from typing import Dict, Iterator, Set, Tuple

from cryptures import Cryptures

from .endpoint_cases import CASES

#: Every operationId in the Cryptures OpenAPI spec (api-docs, 80 operations).
DOCUMENTED_OPERATIONS = {
    # blockchain -- data
    "balance.check",
    "balance.batch",
    "token.transfers",
    "tx.history",
    "portfolio.get",
    "balance-history.get",
    "security.address-check",
    "exchange.rate",
    "exchange.rate.contract",
    "exchange.rate.batch",
    "sentiment.fear-greed",
    "market.global",
    "market.assets",
    "market.tickers",
    "market.tickers.single",
    "market.movers",
    "market.coin.info",
    "market.coin.ohlcv",
    "market.coin.markets",
    "market.coin.social",
    "market.exchanges",
    "market.exchanges.single",
    # blockchain -- lookups
    "tx.hash",
    "block.get",
    "block.latest",
    "tokens.get",
    "utxo.list",
    "utxo.batch",
    # blockchain -- operations
    "tx.send",
    "rpc.gateway",
    "tx.broadcast",
    # blockchain -- wallet / key
    "wallet.generate",
    "address.derive",
    "privatekey.derive",
    # blockchain -- contracts
    "contract.token.deploy",
    "contract.token.mint",
    "contract.token.burn",
    # blockchain -- fee
    "fee.get",
    "fee.gas",
    # blockchain -- nft
    "nft.collection.get",
    "nft.owner.get",
    # blockchain -- storage
    "storage.ipfs.upload",
    # card -- cards and webhooks
    "card.create",
    "card.get",
    "card.setpin",
    "card.fund",
    "card.withdraw",
    "card.terminate",
    "card.block",
    "card.unblock",
    "card.transactions",
    "card.list",
    "card.webhooks.register",
    "card.webhooks.status",
    "card.products.list",
    # card -- balance
    "card.balance.get",
    "card.balance.transactions",
    # card -- tags and reports
    "card.tags.list",
    "card.tags.create",
    "card.tags.update",
    "card.tags.delete",
    "card.tags.set",
    "card.reports.summary",
    # compliance
    "compliance.session.create",
    "compliance.session.get",
    "compliance.sessions.list",
    "compliance.presets.list",
    "compliance.session.documents.get",
    "compliance.webhooks.register",
    "compliance.webhooks.status",
    "compliance.session.status.update",
    "compliance.session.delete",
    "compliance.aml.check",
    "compliance.wallet_screening.create",
    "compliance.wallet_screening.get",
    "compliance.monitoring.enable",
    "compliance.monitoring.disable",
    "compliance.monitoring.list",
    "compliance.session.report.create",
    "compliance.session.report.download",
}

#: Convenience iterators built on top of a covered list endpoint (tested in test_pagination.py).
PAGINATION_HELPERS = {
    "card.balance.list_all_transactions",
    "compliance.sessions.list_all",
    "compliance.monitoring.list_all",
}


def _public_methods(client: Cryptures) -> Iterator[Tuple[str, str]]:
    for domain_name in ("blockchain", "card", "compliance"):
        domain = getattr(client, domain_name)
        for resource_name, resource in vars(domain).items():
            if resource_name.startswith("_"):
                continue
            for method_name, _ in inspect.getmembers(type(resource), predicate=inspect.isfunction):
                if not method_name.startswith("_"):
                    yield f"{domain_name}.{resource_name}.{method_name}", method_name


def test_documented_operation_count() -> None:
    assert len(DOCUMENTED_OPERATIONS) == 80


def test_every_documented_operation_has_a_case() -> None:
    covered = {case.operation_id for case in CASES}
    assert covered == DOCUMENTED_OPERATIONS


def test_every_public_method_has_a_case() -> None:
    client = Cryptures(api_key="k")
    targets = {case.target for case in CASES}
    methods = {qualified for qualified, _ in _public_methods(client)}
    missing = methods - targets - PAGINATION_HELPERS
    assert not missing, f"public SDK methods with no endpoint test: {sorted(missing)}"
    unknown = targets - methods
    assert not unknown, f"endpoint cases pointing at non-existent methods: {sorted(unknown)}"
    assert methods >= PAGINATION_HELPERS


def test_one_sdk_method_per_operation() -> None:
    """Each documented operation maps to exactly one SDK method, and vice versa."""
    op_to_targets: Dict[str, Set[str]] = {}
    for case in CASES:
        op_to_targets.setdefault(case.operation_id, set()).add(case.target)
    assert all(len(targets) == 1 for targets in op_to_targets.values()), op_to_targets
    target_counts = Counter(next(iter(targets)) for targets in op_to_targets.values())
    assert all(count == 1 for count in target_counts.values()), target_counts
    assert len(target_counts) == 80
