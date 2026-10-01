"""Endpoint cases for the card domain (21 operations)."""

from __future__ import annotations

from typing import List

from cryptures import types as t

from ._case import Case

TAG = {"tag_id": "tag_9f1a2b3c-4d5e-6f70-8192-a3b4c5d6e7f8", "name": "Marketing", "color": "#4F46E5"}
WEBHOOK_REGISTRATION = {
    "url": "https://example.com/webhooks/card",
    "secret": "3f1a9c2e7b6d4058a1c9e3f70b8d2a5c6e9f1b3d7a0c5e8f2b4d6a9c1e3f5b7d",
}
WEBHOOK_STATUS = {
    "registered": True,
    "url": "https://example.com/webhooks/card",
    "registered_at": "2026-09-12T18:04:33Z",
}
CARD = {
    "card_id": "card_a1b2c3d4",
    "product_code": "us_493_visa_bin",
    "brand": "visa",
    "type": "virtual",
    "currency": "USD",
    "status": "active",
    "name_on_card": "Jane Doe",
    "email": "a1b2c3d4-e5f6-4789-a012-3456789abcde@placeholder.invalid",
    "last_four": "1111",
    "expiry_month": "08",
    "expiry_year": "2031",
    "balance": {"amount": 10000000, "display_amount": 10, "currency": "USD"},
    "card_number": "4111111111111111",
    "cvv": "123",
    "cardnumber": "4111111111111111",
    "expiredate": "08/31",
    "created_at": "2026-08-29T00:00:00Z",
    "tags": [TAG],
}

CARD_CASES: List[Case] = [
    # ============================================================= card.cards
    Case(
        "card.create",
        "card.cards.create",
        lambda c: c.card.cards.create(
            product_code="us_493_visa_bin",
            first_name="Jane",
            last_name="Doe",
            email="jane@example.com",
            initial_load=20,
            tags=["Marketing"],
        ),
        "POST",
        "/api/v1/card/cards/create",
        json={
            "product_code": "us_493_visa_bin",
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane@example.com",
            "initial_load": 20,
            "tags": ["Marketing"],
        },
        response={
            "status": "success",
            "message": "Card created successfully.",
            "data": {"card_id": "card_a1b2c3d4", "status": "active", "last_four": "4242", "tags": [TAG]},
        },
        check=lambda r: (
            isinstance(r, t.CardResponse) and r.data.card_id == "card_a1b2c3d4" and r.data.tags[0].name
        ),
    ),
    Case(
        "card.get",
        "card.cards.get",
        lambda c: c.card.cards.get("card_a1b2c3d4"),
        "GET",
        "/api/v1/card/cards/card_a1b2c3d4",
        response={"status": "success", "message": "Card fetched successfully.", "data": CARD},
        check=lambda r: (
            isinstance(r.data, t.Card)
            and r.data.balance.amount == 10000000
            and r.data.cardnumber == r.data.card_number
        ),
    ),
    Case(
        "card.setpin",
        "card.cards.set_pin",
        lambda c: c.card.cards.set_pin("card_atm_1a2b3c", "654321"),
        "POST",
        "/api/v1/card/cards/card_atm_1a2b3c/pin",
        json={"pin": "654321"},
        response={"status": "success", "message": "Card PIN set successfully."},
        check=lambda r: isinstance(r, t.CardSetPinResponse) and r.status == "success",
    ),
    Case(
        "card.fund",
        "card.cards.fund",
        lambda c: c.card.cards.fund("card_a1b2c3d4", 10),
        "POST",
        "/api/v1/card/cards/card_a1b2c3d4/fund",
        json={"amount": 10},
        response={
            "status": "success",
            "data": {"card_id": "card_a1b2c3d4", "amount": 10000000, "display_amount": 10},
        },
        check=lambda r: isinstance(r, t.CardFundResponse) and r.data.amount == 10000000,
    ),
    Case(
        "card.withdraw",
        "card.cards.withdraw",
        lambda c: c.card.cards.withdraw("card_a1b2c3d4", 10),
        "POST",
        "/api/v1/card/cards/card_a1b2c3d4/withdraw",
        json={"amount": 10},
        response={
            "status": "success",
            "message": "Card withdrawal completed successfully.",
            "data": {"card_id": "card_a1b2c3d4", "amount": 10000000, "display_amount": 10},
        },
        check=lambda r: isinstance(r, t.CardWithdrawResponse) and r.data.display_amount == 10,
    ),
    Case(
        "card.terminate",
        "card.cards.terminate",
        lambda c: c.card.cards.terminate("card_a1b2c3d4"),
        "POST",
        "/api/v1/card/cards/card_a1b2c3d4/terminate",
        response={
            "status": "success",
            "message": "Card terminated successfully.",
            "data": {"card_id": "card_a1b2c3d4", "status": "terminated"},
        },
        check=lambda r: isinstance(r, t.CardStatusChangeResponse) and r.data.status == "terminated",
    ),
    Case(
        "card.block",
        "card.cards.block",
        lambda c: c.card.cards.block("card_a1b2c3d4"),
        "POST",
        "/api/v1/card/cards/card_a1b2c3d4/block",
        response={"status": "success", "data": {"card_id": "card_a1b2c3d4", "status": "blocked"}},
        check=lambda r: r.data.status == "blocked",
    ),
    Case(
        "card.unblock",
        "card.cards.unblock",
        lambda c: c.card.cards.unblock("card_a1b2c3d4"),
        "POST",
        "/api/v1/card/cards/card_a1b2c3d4/unblock",
        response={"status": "success", "data": {"card_id": "card_a1b2c3d4", "status": "active"}},
        check=lambda r: r.data.status == "active",
    ),
    Case(
        "card.transactions",
        "card.cards.list_transactions",
        lambda c: c.card.cards.list_transactions("card_a1b2c3d4", page_num=1),
        "GET",
        "/api/v1/card/cards/card_a1b2c3d4/transactions",
        query={"pageNum": "1"},
        response={
            "status": "success",
            "message": "Transactions fetched successfully.",
            "data": {
                "transactions": [
                    {
                        "id": "260820000000002879",
                        "card_id": "card_a1b2c3d4",
                        "type": "authorization",
                        "status": "completed",
                        "amount": 460000,
                        "display_amount": 0.46,
                        "currency": "USD",
                        "merchant_name": "Grab",
                        "created_at": "2026-08-20T05:55:00Z",
                    }
                ],
                "pagination": {"type": "page", "page_num": 1, "page_size": 1, "total": 1, "has_more": False},
            },
        },
        check=lambda r: (
            isinstance(r, t.CardTransactionsResponse)
            and r.data.transactions[0].merchant_name == "Grab"
            and r.data.pagination.has_more is False
        ),
    ),
    Case(
        "card.list",
        "card.cards.list",
        lambda c: c.card.cards.list(),
        "GET",
        "/api/v1/card/cards",
        response={
            "data": [
                {
                    "card_id": "card_a1b2c3d4",
                    "product_code": "us_493_visa_bin",
                    "email": "jane@example.com",
                    "first_name": "Jane",
                    "last_name": "Doe",
                    "status": "active",
                    "last_four": "4242",
                    "label": None,
                    "created_at": "2026-08-28T00:00:00Z",
                    "tags": [TAG],
                }
            ]
        },
        check=lambda r: (
            isinstance(r, t.CardList) and r.data[0].email == "jane@example.com" and r.data[0].label is None
        ),
    ),
    Case(
        "card.tags.set",
        "card.cards.set_tags",
        lambda c: c.card.cards.set_tags("card_a1b2c3d4", ["Marketing", "VIP"]),
        "PUT",
        "/api/v1/card/cards/card_a1b2c3d4/tags",
        json={"tags": ["Marketing", "VIP"]},
        response={"tags": [TAG]},
        check=lambda r: isinstance(r, t.CardTags) and r.tags[0].tag_id == TAG["tag_id"],
    ),
    Case(
        "card.products.list",
        "card.cards.list_products",
        lambda c: c.card.cards.list_products(),
        "GET",
        "/api/v1/card/products",
        response={
            "products": [
                {
                    "product_code": "us_493_visa_atm",
                    "display_name": "US Visa ATM Card",
                    "min_load_usd": None,
                    "max_load_usd": None,
                    "issuance_fee_usd": 1,
                    "fund_fee_flat_usd": 0,
                    "fund_fee_pct": 0,
                    "annual_fee_usd": 9,
                    "disallow_initial_load": True,
                }
            ]
        },
        check=lambda r: (
            isinstance(r.products[0], t.CardProduct)
            and r.products[0].disallow_initial_load
            and r.products[0].min_load_usd is None
        ),
    ),
    # ========================================================== card.webhooks
    Case(
        "card.webhooks.register",
        "card.webhooks.register",
        lambda c: c.card.webhooks.register("https://example.com/webhooks/card"),
        "POST",
        "/api/v1/card/webhooks/register",
        json={"url": "https://example.com/webhooks/card"},
        response=WEBHOOK_REGISTRATION,
        check=lambda r: isinstance(r, t.WebhookRegistration) and len(r.secret) == 64,
    ),
    Case(
        "card.webhooks.status",
        "card.webhooks.status",
        lambda c: c.card.webhooks.status(),
        "GET",
        "/api/v1/card/webhooks/status",
        response=WEBHOOK_STATUS,
        check=lambda r: isinstance(r, t.WebhookStatus) and r.registered is True,
    ),
    # =========================================================== card.balance
    Case(
        "card.balance.get",
        "card.balance.get",
        lambda c: c.card.balance.get(),
        "GET",
        "/api/v1/card/balance",
        response={"balance_usd": 42.5, "updated_at": "2026-08-29T00:00:00Z"},
        check=lambda r: isinstance(r, t.CardBalance) and r.balance_usd == 42.5,
    ),
    Case(
        "card.balance.transactions",
        "card.balance.list_transactions",
        lambda c: c.card.balance.list_transactions(page=1, limit=50),
        "GET",
        "/api/v1/card/balance/transactions",
        query={"page": "1", "limit": "50"},
        response={
            "data": [
                {
                    "id": "bl_9f1a2b3c",
                    "type": "card_fund_debit",
                    "amount_usd": 11.4,
                    "related_reference": "card_a1b2c3d4",
                    "status": "completed",
                    "created_at": "2026-08-29T00:00:01Z",
                }
            ],
            "page": 1,
            "limit": 50,
            "total": 1,
        },
        check=lambda r: isinstance(r, t.BalanceTransactionList) and r.data[0].type == "card_fund_debit",
    ),
    # ============================================================== card.tags
    Case(
        "card.tags.list",
        "card.tags.list",
        lambda c: c.card.tags.list(),
        "GET",
        "/api/v1/card/tags",
        response={
            "data": [{**TAG, "created_at": "2026-08-29T00:00:00Z", "updated_at": "2026-08-29T00:00:00Z"}]
        },
        check=lambda r: isinstance(r, t.TagList) and r.data[0].color == "#4F46E5",
    ),
    Case(
        "card.tags.create",
        "card.tags.create",
        lambda c: c.card.tags.create("Marketing", color="#4F46E5"),
        "POST",
        "/api/v1/card/tags",
        status=201,
        json={"name": "Marketing", "color": "#4F46E5"},
        response={**TAG, "created_at": "2026-08-29T00:00:00Z", "updated_at": "2026-08-29T00:00:00Z"},
        check=lambda r: isinstance(r, t.Tag) and r.name == "Marketing",
    ),
    Case(
        "card.tags.update",
        "card.tags.update",
        lambda c: c.card.tags.update(TAG["tag_id"], color="#DC2626"),
        "PATCH",
        f"/api/v1/card/tags/{TAG['tag_id']}",
        json={"color": "#DC2626"},
        response={**TAG, "color": "#DC2626", "updated_at": "2026-08-29T01:00:00Z"},
        check=lambda r: isinstance(r, t.TagUpdated) and r.color == "#DC2626",
    ),
    Case(
        "card.tags.delete",
        "card.tags.delete",
        lambda c: c.card.tags.delete(TAG["tag_id"]),
        "DELETE",
        f"/api/v1/card/tags/{TAG['tag_id']}",
        response={"deleted": True},
        check=lambda r: isinstance(r, t.TagDeleted) and r.deleted is True,
    ),
    # =========================================================== card.reports
    Case(
        "card.reports.summary",
        "card.reports.summary",
        lambda c: c.card.reports.summary(from_="2026-01-01T00:00:00Z", to="2026-09-01T00:00:00Z"),
        "GET",
        "/api/v1/card/reports/summary",
        query={"from": "2026-01-01T00:00:00Z", "to": "2026-09-01T00:00:00Z"},
        response={
            "range": {"from": "2026-01-01T00:00:00Z", "to": "2026-09-01T00:00:00Z"},
            "totals": {"funded_usd": 1250, "withdrawn_usd": 300, "net_usd": 950, "card_count": 4},
            "unattributed": {"funded_usd": 0},
            "by_month": [{"month": "2026-08", "funded_usd": 200, "withdrawn_usd": 0, "net_usd": 200}],
            "by_type": [
                {
                    "product_code": "visa_standard",
                    "funded_usd": 1250,
                    "withdrawn_usd": 300,
                    "net_usd": 950,
                    "card_count": 4,
                }
            ],
            "by_tag": [{**TAG, "funded_usd": 400, "withdrawn_usd": 0, "net_usd": 400, "card_count": 2}],
            "untagged": {"funded_usd": 850, "withdrawn_usd": 300, "net_usd": 550, "card_count": 2},
            "by_card": [
                {
                    "card_id": "card_a1b2c3d4",
                    "first_name": "Jane",
                    "last_name": "Doe",
                    "last_four": "4242",
                    "product_code": "visa_standard",
                    "tags": [],
                    "funded_usd": 300,
                    "withdrawn_usd": 0,
                    "net_usd": 300,
                }
            ],
        },
        check=lambda r: (
            isinstance(r, t.ReportSummary)
            and r.range.from_ == "2026-01-01T00:00:00Z"
            and r.totals.card_count == 4
            and r.by_card[0].net_usd == 300
        ),
    ),
]
