"""The spec file is well formed and every method it names exists on the backend classes."""

from __future__ import annotations

import re
from collections import Counter

import yaml
from merchant_agent.backend import MerchantBackend
from shopping_agent.backend import StorefrontBackend

from commerce_conformance import spec_path

SHOPPING_TOOLS = {
    "search_products", "get_product_details", "add_to_cart", "update_cart_item",
    "remove_from_cart", "get_cart", "checkout", "get_orders", "get_order_status",
    "search_policies", "get_preferences", "get_fulfillment_options", "present_products",
    "present_comparison", "present_plan", "present_guide", "present_order_status",
    "present_disclosure", "present_suggestions", "recall_memories", "save_memory",
}  # fmt: skip
MERCHANT_TOOLS = {
    "get_business_snapshot", "query_metrics", "search_listings", "get_listing",
    "get_inventory_alerts", "get_order_issues", "get_campaign_performance",
    "get_pricing_context", "stage_price_update", "stage_inventory_action",
    "stage_listing_update", "stage_promotion", "stage_campaign", "get_pending_changes",
    "apply_change", "discard_change", "present_metrics", "present_digest",
    "present_change_preview", "present_suggestions", "recall_memories", "save_memory",
}  # fmt: skip


def load():
    return yaml.safe_load(spec_path().read_text())


def test_ids_are_unique_and_shaped():
    spec = load()
    ids = [s["id"] for a in spec["areas"] for s in a["statements"]]
    assert len(ids) == len(set(ids)), Counter(ids).most_common(3)
    for sid in ids:
        assert re.fullmatch(r"(BE-S|BE-M|EX-S|EX-M|HS-S|HS-M|RT|HOST|E2E)-\d\d", sid), sid
    assert len(ids) == 137


def test_every_statement_has_text_and_source():
    for area in load()["areas"]:
        for s in area["statements"]:
            assert s["text"].strip() and s["source"].strip(), s["id"]


# Methods the hardening and end-to-end statements propose and the reference does not have
# (the shopper order-action proposal, anthropics/commerce-agents#22).
PROPOSED = {"request_order_action", "get_order_requests", "resolve_order_request"}


def test_named_methods_exist_on_the_backends_or_as_tools():
    known = (
        {n for n in dir(StorefrontBackend) if not n.startswith("_")}
        | {n for n in dir(MerchantBackend) if not n.startswith("_")}
        | SHOPPING_TOOLS
        | MERCHANT_TOOLS
        | {"apply", "stage", "checkout_handoff"}
    )
    for area in load()["areas"]:
        allowed = known | PROPOSED if area["id"] in {"HS", "E2E"} else known
        for s in area["statements"]:
            for m in s.get("methods") or []:
                assert m in allowed, f"{s['id']} names unknown method {m}"
