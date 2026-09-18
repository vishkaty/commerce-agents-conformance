"""What a target must tell the suites about itself: how to build a fresh backend and
which fixture ids exercise which statement. A fact left None skips the statements that
need it, and the report shows that as a gap of the target, not of the suite."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

import pytest
from merchant_agent import MerchantAgentConfig, MerchantSessionContext
from shopping_agent import ShoppingAgentConfig, ShoppingSessionContext


def spec(*ids: str):
    """Mark a test with the spec statements it pins."""
    return pytest.mark.spec(*ids)


@dataclass
class StorefrontFacts:
    search_query: str  # matches at least two listings, one of them plain_product_id
    plain_product_id: str  # in stock, no options: the cart takes its id
    family_id: str | None = None  # a product with options
    variant_id: str | None = None  # an in-stock variant of family_id
    out_of_stock_variant_id: str | None = None
    unknown_id: str = "nope-does-not-exist"
    unshipped_order_id: str | None = None  # an order of user_with_orders still processing
    shipped_order_id: str | None = None  # an order of user_with_orders already shipped
    policy_query: str = "return"
    policy_miss_query: str = "zqxjv"
    user_with_orders: str | None = None  # a user id whose get_orders is non-empty
    guest_user: str = "conformance-guest"
    other_users_order_id: str | None = None  # an order that belongs to someone else
    hostile_policy_query: str | None = None  # a query whose passage carries instructions
    hostile_order_user_id: str | None = None  # a user whose order item title is hostile
    hostile_product_id: str | None = None  # a listing whose text carries instructions
    hostile_markers: tuple[str, ...] = ("</storefront_data>", "\u200b")  # what sanitize_text strips
    expects_handoff: bool = False  # checkout_handoff returns a URL for a non-empty cart


@dataclass
class MerchantFacts:
    search_query: str
    plain_listing_id: str  # priced and stocked on itself
    family_listing_id: str | None = None
    variant_listing_id: str | None = None
    unknown_id: str = "nope-does-not-exist"
    metric: str = "sales"
    unsupported_segment: str = "zqxjv-segment"
    operator: str = "conformance-operator"
    merchant_id: str = "conformance-merchant"
    restock_quantity: int = 5
    hostile_listing_id: str | None = None
    unknown_campaign_id: str = "camp-does-not-exist"


@dataclass
class Target:
    name: str
    make_storefront: Callable[[], Awaitable[Any] | Any] | None = None
    shopping_config: ShoppingAgentConfig = field(default_factory=ShoppingAgentConfig)
    storefront_facts: StorefrontFacts | None = None
    make_merchant: Callable[[], Awaitable[Any] | Any] | None = None
    merchant_config: MerchantAgentConfig = field(default_factory=MerchantAgentConfig)
    merchant_facts: MerchantFacts | None = None
    # make the platform refuse writes after n successful ones (0 = all of them)
    break_merchant_writes: Callable[[Any, int], None] | None = None
    # remove a listing from the platform behind the backend's back
    remove_listing_from_platform: Callable[[Any, str], None] | None = None
    # plant hostile text in a fulfillment option label and a preference value (EX-S-22)
    plant_hostile_fulfillment: Callable[[Any], None] | None = None
    plant_hostile_preference: Callable[[Any, str], None] | None = None
    # make a product unpurchasable on the platform behind the backend's back (cart re-validation)
    make_unpurchasable: Callable[[Any, str], None] | None = None
    # move a listing's price on the platform behind the backend's back (staleness check)
    move_price_on_platform: Callable[[Any, str, float], None] | None = None
    # the merchant backend that sees the storefront's order requests
    merchant_for_requests: Callable[[Any], Any] | None = None
    # a new merchant backend instance over the same store and ledger (a restart)
    reopen_merchant: Callable[[Any], Any] | None = None
    # make the next apply die after the platform write, before the stamp (idempotent apply)
    interrupt_apply_before_stamp: Callable[[Any], None] | None = None
    notes: str = ""

    async def storefront(self) -> Any:
        if self.make_storefront is None:
            pytest.skip(f"{self.name}: no storefront backend")
        result = self.make_storefront()
        return await result if hasattr(result, "__await__") else result

    async def merchant(self) -> Any:
        if self.make_merchant is None:
            pytest.skip(f"{self.name}: no merchant backend")
        result = self.make_merchant()
        return await result if hasattr(result, "__await__") else result

    def shopper(
        self, user_id: str | None = None, session_id: str = "conf-s"
    ) -> ShoppingSessionContext:
        facts = self.storefront_facts
        user = user_id or (
            facts.user_with_orders if facts and facts.user_with_orders else "conformance-user"
        )
        return ShoppingSessionContext(session_id=session_id, user_id=user)

    def operator(
        self,
        session_id: str = "conf-m",
        operator: str | None = None,
        merchant_id: str | None = None,
    ) -> MerchantSessionContext:
        facts = self.merchant_facts
        return MerchantSessionContext(
            session_id=session_id,
            merchant_id=merchant_id or (facts.merchant_id if facts else "conformance-merchant"),
            operator=operator or (facts.operator if facts else "conformance-operator"),
        )


async def managed(coro: Any, what: str) -> Any:
    """Await a stage call; a backend that raises ChangeNotApplicable does not manage that
    system here (the contract's own escape hatch), so the statement is skipped for it."""
    from merchant_agent.changes import ChangeNotApplicable

    try:
        return await coro
    except ChangeNotApplicable as unmanaged:
        pytest.skip(f"{what} is not managed by this backend: {unmanaged}")


def need(value: Any, what: str) -> Any:
    """Skip the statement when the target has no fact for it."""
    if value is None:
        pytest.skip(f"target has no {what}")
    return value
