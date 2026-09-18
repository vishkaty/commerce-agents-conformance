"""BE-S: the StorefrontBackend contract, over any implementation a target names."""

from __future__ import annotations

import asyncio
import json

import pytest
from shopping_agent import SearchFilters
from shopping_agent.backend import Unavailable

from commerce_conformance.facts import Target, need, spec


class StorefrontConformance:
    """Subclass in a target file and provide a ``target`` fixture."""

    @spec("BE-S-01")
    async def test_search_is_bounded_ordered_and_empty_on_miss(self, target: Target):
        backend, facts = (
            await target.storefront(),
            need(target.storefront_facts, "storefront facts"),
        )
        session = target.shopper()
        results = await backend.search_products(session, facts.search_query, limit=2)
        assert 1 <= len(results) <= 2
        assert len({p.product_id for p in results}) == len(results)
        assert await backend.search_products(session, "zqxjv wqpl", limit=8) == []

    @spec("BE-S-02")
    async def test_search_returns_families_not_variants(self, target: Target):
        backend, facts = (
            await target.storefront(),
            need(target.storefront_facts, "storefront facts"),
        )
        results = await backend.search_products(target.shopper(), facts.search_query, limit=25)
        assert all(not p.variant_of for p in results), "a variant appeared as a result"
        assert all(not p.option_values for p in results)

    @spec("BE-S-03")
    async def test_details_known_and_unknown(self, target: Target):
        backend, facts = (
            await target.storefront(),
            need(target.storefront_facts, "storefront facts"),
        )
        session = target.shopper()
        record = await backend.get_product_details(session, facts.plain_product_id)
        assert record is not None and record.product_id == facts.plain_product_id
        assert record.title and record.price >= 0
        assert not record.has_options and record.variants == []
        assert await backend.get_product_details(session, facts.unknown_id) is None

    @spec("BE-S-04")
    async def test_family_details_carry_variants(self, target: Target):
        backend, facts = (
            await target.storefront(),
            need(target.storefront_facts, "storefront facts"),
        )
        family_id = need(facts.family_id, "family")
        session = target.shopper()
        family = await backend.get_product_details(session, family_id)
        assert family is not None and family.has_options and family.variants
        for variant in family.variants:
            assert variant.variant_of == family_id
            assert variant.option_values and set(variant.option_values) <= set(family.options)
            assert variant.product_id != family_id
        one = await backend.get_product_details(session, family.variants[0].product_id)
        assert one is not None and one.product_id == family.variants[0].product_id
        assert one.variant_of == family_id and one.variants == []

    @spec("BE-S-05")
    async def test_family_price_and_stock_follow_variants(self, target: Target):
        backend, facts = (
            await target.storefront(),
            need(target.storefront_facts, "storefront facts"),
        )
        family = await backend.get_product_details(
            target.shopper(), need(facts.family_id, "family")
        )
        assert family is not None
        in_stock = [v for v in family.variants if v.in_stock]
        assert family.in_stock == bool(in_stock)
        if in_stock:
            assert family.price == pytest.approx(min(v.price for v in in_stock))

    @spec("BE-S-06")
    async def test_fresh_session_cart_is_empty(self, target: Target):
        backend = await target.storefront()
        cart = await backend.get_cart(target.shopper(session_id="conf-fresh"))
        assert cart.items == [] and cart.item_count == 0 and cart.subtotal == 0

    @spec("BE-S-07")
    async def test_add_returns_the_cart_and_lines_belong_to_the_session(self, target: Target):
        backend, facts = (
            await target.storefront(),
            need(target.storefront_facts, "storefront facts"),
        )
        a, b = target.shopper(session_id="conf-a"), target.shopper(session_id="conf-b")
        cart = await backend.add_to_cart(a, facts.plain_product_id, 1)
        assert [i.product_id for i in cart.items] == [facts.plain_product_id]
        assert cart.items[0].quantity == 1 and cart.items[0].price >= 0
        assert (await backend.get_cart(a)).item_count == 1
        assert (await backend.get_cart(b)).items == []

    @spec("BE-S-08")
    async def test_out_of_stock_variant_is_unavailable_and_unwritten(self, target: Target):
        backend, facts = (
            await target.storefront(),
            need(target.storefront_facts, "storefront facts"),
        )
        oos = need(facts.out_of_stock_variant_id, "out-of-stock variant")
        session = target.shopper(session_id="conf-oos")
        with pytest.raises(Unavailable) as raised:
            await backend.add_to_cart(session, oos, 1)
        assert oos in str(raised.value)
        assert (await backend.get_cart(session)).items == []

    @spec("BE-S-09")
    async def test_update_sets_quantity_and_ignores_unknown_lines(self, target: Target):
        backend, facts = (
            await target.storefront(),
            need(target.storefront_facts, "storefront facts"),
        )
        session = target.shopper(session_id="conf-upd")
        await backend.add_to_cart(session, facts.plain_product_id, 1)
        cart = await backend.update_cart_item(session, facts.plain_product_id, 3)
        assert next(i for i in cart.items if i.product_id == facts.plain_product_id).quantity == 3
        before = await backend.get_cart(session)
        after = await backend.update_cart_item(session, facts.unknown_id, 5)
        assert [(i.product_id, i.quantity) for i in after.items] == [
            (i.product_id, i.quantity) for i in before.items
        ]

    @spec("BE-S-10")
    async def test_remove_drops_the_line_and_ignores_unknown(self, target: Target):
        backend, facts = (
            await target.storefront(),
            need(target.storefront_facts, "storefront facts"),
        )
        session = target.shopper(session_id="conf-rm")
        await backend.add_to_cart(session, facts.plain_product_id, 2)
        untouched = await backend.remove_from_cart(session, facts.unknown_id)
        assert untouched.item_count == 2
        cart = await backend.remove_from_cart(session, facts.plain_product_id)
        assert all(i.product_id != facts.plain_product_id for i in cart.items)

    @spec("BE-S-11")
    async def test_preferences_for_customer_and_guest(self, target: Target):
        backend, facts = (
            await target.storefront(),
            need(target.storefront_facts, "storefront facts"),
        )
        known = await backend.get_preferences(target.shopper())
        assert known.user_id
        guest = await backend.get_preferences(
            target.shopper(user_id=facts.guest_user, session_id="conf-g")
        )
        assert guest.user_id == facts.guest_user

    @spec("BE-S-12")
    async def test_orders_are_own_newest_first_and_bounded(self, target: Target):
        backend, facts = (
            await target.storefront(),
            need(target.storefront_facts, "storefront facts"),
        )
        user = need(facts.user_with_orders, "user with orders")
        orders = await backend.get_orders(target.shopper(user_id=user), limit=5)
        assert 1 <= len(orders) <= 5
        placed = [o.placed_at for o in orders]
        assert placed == sorted(placed, reverse=True)
        assert (
            await backend.get_orders(target.shopper(user_id=facts.guest_user, session_id="conf-g2"))
            == []
        )

    @spec("BE-S-13")
    async def test_unknown_order_is_none(self, target: Target):
        backend, facts = (
            await target.storefront(),
            need(target.storefront_facts, "storefront facts"),
        )
        assert await backend.get_order(target.shopper(), facts.unknown_id) is None

    @spec("BE-S-14")
    async def test_policies_match_and_miss(self, target: Target):
        backend, facts = (
            await target.storefront(),
            need(target.storefront_facts, "storefront facts"),
        )
        session = target.shopper()
        hits = await backend.search_policies(session, facts.policy_query)
        assert hits and all(p.content and p.policy_id for p in hits)
        assert await backend.search_policies(session, facts.policy_miss_query) == []

    @spec("BE-S-15")
    async def test_fulfillment_options_for_known_ids(self, target: Target):
        backend, facts = (
            await target.storefront(),
            need(target.storefront_facts, "storefront facts"),
        )
        session = target.shopper(session_id="conf-ful")
        options = await backend.get_fulfillment_options(
            session, [facts.plain_product_id, facts.unknown_id]
        )
        assert isinstance(options, list)
        for option in options:
            assert option.method in {"delivery", "pickup", "shipping"} and option.eta

    @spec("BE-S-16")
    async def test_checkout_handoff_is_urls_or_nothing_and_nothing_places_an_order(
        self, target: Target
    ):
        backend, facts = (
            await target.storefront(),
            need(target.storefront_facts, "storefront facts"),
        )
        session = target.shopper(session_id="conf-co")
        cart = await backend.add_to_cart(session, facts.plain_product_id, 1)
        handoffs = await backend.checkout_handoff(session, cart)
        assert isinstance(handoffs, list)
        for handoff in handoffs:
            assert handoff.url.startswith("https://")
        assert facts.expects_handoff == bool(handoffs)
        assert not any(
            name in {"place_order", "charge", "pay"}
            for name in dir(backend)
            if not name.startswith("_")
        )
        assert (await backend.get_cart(session)).item_count == 1, (
            "handoff must not consume the cart"
        )

    # -- statements added 2026-09-09: filters, odd input, integrity, isolation ----------

    @spec("BE-S-17")
    async def test_search_honours_max_price_and_price_sort(self, target: Target):
        backend, facts = (
            await target.storefront(),
            need(target.storefront_facts, "storefront facts"),
        )
        session = target.shopper()
        all_hits = await backend.search_products(session, facts.search_query, limit=25)
        assert all_hits
        cap = sorted(p.price for p in all_hits)[len(all_hits) // 2]
        capped = await backend.search_products(
            session, facts.search_query, SearchFilters(max_price=cap), limit=25
        )
        assert capped and all(p.price <= cap for p in capped)
        ordered = await backend.search_products(
            session, facts.search_query, SearchFilters(sort="price_asc"), limit=25
        )
        prices = [p.price for p in ordered]
        assert prices == sorted(prices)

    @spec("BE-S-18")
    async def test_odd_input_never_raises(self, target: Target):
        backend = await target.storefront()
        session = target.shopper()
        odd = [
            "",
            " ",
            "x" * 2000,
            "café ☕ 日本",
            ".*",
            "../../etc/passwd",
            "'; DROP TABLE p;--",
            "%",
        ]
        for query in odd:
            assert isinstance(await backend.search_products(session, query, limit=5), list)
        for product_id in odd:
            assert await backend.get_product_details(session, product_id) is None

    @spec("BE-S-19")
    async def test_second_add_merges_into_one_line(self, target: Target):
        backend, facts = (
            await target.storefront(),
            need(target.storefront_facts, "storefront facts"),
        )
        session = target.shopper(session_id="conf-merge")
        await backend.add_to_cart(session, facts.plain_product_id, 1)
        cart = await backend.add_to_cart(session, facts.plain_product_id, 2)
        lines = [i for i in cart.items if i.product_id == facts.plain_product_id]
        assert len(lines) == 1 and lines[0].quantity == 3

    @spec("BE-S-20")
    async def test_cart_line_matches_the_product_record(self, target: Target):
        backend, facts = (
            await target.storefront(),
            need(target.storefront_facts, "storefront facts"),
        )
        session = target.shopper(session_id="conf-integrity")
        record = await backend.get_product_details(session, facts.plain_product_id)
        assert record is not None
        cart = await backend.add_to_cart(session, facts.plain_product_id, 1)
        line = next(i for i in cart.items if i.product_id == facts.plain_product_id)
        assert line.title == record.title
        assert line.price == pytest.approx(record.price)
        assert cart.currency.upper() == record.currency.upper()

    @spec("BE-S-21")
    async def test_family_record_is_internally_consistent(self, target: Target):
        backend, facts = (
            await target.storefront(),
            need(target.storefront_facts, "storefront facts"),
        )
        family = await backend.get_product_details(
            target.shopper(), need(facts.family_id, "family")
        )
        assert family is not None and family.options
        assert all(values for values in family.options.values())
        seen: set[tuple[tuple[str, str], ...]] = set()
        for variant in family.variants:
            assert set(variant.option_values) == set(family.options), variant.product_id
            for name, value in variant.option_values.items():
                assert value in family.options[name], (variant.product_id, name, value)
            key = tuple(sorted(variant.option_values.items()))
            assert key not in seen, f"two variants share {dict(key)}"
            seen.add(key)

    @spec("BE-S-22")
    async def test_another_customers_order_is_none(self, target: Target):
        backend, facts = (
            await target.storefront(),
            need(target.storefront_facts, "storefront facts"),
        )
        other = need(facts.other_users_order_id, "another customer's order")
        assert await backend.get_order(target.shopper(), other) is None

    @spec("BE-S-23")
    async def test_orders_are_well_formed(self, target: Target):
        backend, facts = (
            await target.storefront(),
            need(target.storefront_facts, "storefront facts"),
        )
        user = need(facts.user_with_orders, "user with orders")
        orders = await backend.get_orders(target.shopper(user_id=user), limit=5)
        assert orders
        for order in orders:
            assert order.order_id and order.status and order.placed_at and order.total >= 0
            assert order.items and all(i.quantity >= 1 and i.product_id for i in order.items)
            one = await backend.get_order(target.shopper(user_id=user), order.order_id)
            assert one is not None and one.order_id == order.order_id

    @spec("BE-S-24")
    async def test_policies_are_case_insensitive_and_stable(self, target: Target):
        backend, facts = (
            await target.storefront(),
            need(target.storefront_facts, "storefront facts"),
        )
        session = target.shopper()
        lower = [
            p.policy_id for p in await backend.search_policies(session, facts.policy_query.lower())
        ]
        upper = [
            p.policy_id for p in await backend.search_policies(session, facts.policy_query.upper())
        ]
        again = [
            p.policy_id for p in await backend.search_policies(session, facts.policy_query.lower())
        ]
        assert lower and lower == upper == again

    @spec("BE-S-25")
    async def test_concurrent_adds_both_land(self, target: Target):
        backend, facts = (
            await target.storefront(),
            need(target.storefront_facts, "storefront facts"),
        )
        session = target.shopper(session_id="conf-race")
        await asyncio.gather(
            backend.add_to_cart(session, facts.plain_product_id, 1),
            backend.add_to_cart(session, facts.plain_product_id, 1),
        )
        cart = await backend.get_cart(session)
        line = next(i for i in cart.items if i.product_id == facts.plain_product_id)
        assert line.quantity == 2, "a lost update: the two adds raced"

    @spec("BE-S-26")
    async def test_disclosure_is_none_or_for_the_product(self, target: Target):
        backend, facts = (
            await target.storefront(),
            need(target.storefront_facts, "storefront facts"),
        )
        session = target.shopper()
        for product_id in (facts.plain_product_id, facts.unknown_id):
            disclosure = await backend.get_disclosure(session, product_id)
            assert disclosure is None or (
                disclosure.product_id == product_id and disclosure.rows and disclosure.title
            )

    @spec("BE-S-27")
    async def test_account_context_is_none_or_small(self, target: Target):
        backend = await target.storefront()
        context = await backend.get_account_context(target.shopper())
        if context is not None:
            assert isinstance(context, dict)
            assert len(json.dumps(context, default=str)) <= 2000, "sent on every request"

    @spec("BE-S-28")
    async def test_policies_and_fulfillment_never_raise_on_odd_input(self, target: Target):
        backend, facts = (
            await target.storefront(),
            need(target.storefront_facts, "storefront facts"),
        )
        session = target.shopper()
        odd = ["", " ", "x" * 2000, "café ☕ 日本", ".*", "../../etc/passwd", "%", "'; --"]
        for query in odd:
            assert isinstance(await backend.search_policies(session, query), list)
        options = await backend.get_fulfillment_options(session, odd + [facts.plain_product_id])
        assert isinstance(options, list)

    # -- hardening proposals -----------------------------------------------------------

    @spec("HS-S-07")
    async def test_handoff_refuses_a_line_that_became_unpurchasable(self, target: Target):
        backend, facts = (
            await target.storefront(),
            need(target.storefront_facts, "storefront facts"),
        )
        spoil = need(target.make_unpurchasable, "a way to make a product unpurchasable")
        session = target.shopper(session_id="conf-hs7")
        await backend.add_to_cart(session, facts.plain_product_id, 1)
        spoil(backend, facts.plain_product_id)
        with pytest.raises(Unavailable) as raised:
            await backend.checkout_handoff(session, await backend.get_cart(session))
        assert facts.plain_product_id in str(raised.value)

    @spec("HS-S-08")
    async def test_order_request_is_recorded_for_own_orders_only(self, target: Target):
        backend, facts = (
            await target.storefront(),
            need(target.storefront_facts, "storefront facts"),
        )
        request_action = getattr(backend, "request_order_action", None)
        if request_action is None:
            pytest.skip("backend has no request_order_action")
        user = need(facts.user_with_orders, "user with orders")
        order_id = need(facts.unshipped_order_id, "unshipped order")
        session = target.shopper(user_id=user, session_id="conf-req")
        request = await request_action(session, order_id, "problem", [], "box arrived dented")
        assert request.status == "requested" and request.order_id == order_id
        assert request.request_id in {
            r.request_id for r in await backend.get_order_requests(session)
        }
        assert (await backend.get_order(session, order_id)) is not None, "nothing written"
        guest = target.shopper(user_id=facts.guest_user, session_id="conf-req-g")
        with pytest.raises(ValueError):
            await request_action(guest, order_id, "problem", [], "not mine")
        with pytest.raises(ValueError):
            await request_action(session, facts.unknown_id, "problem", [], "no such order")

    @spec("HS-S-09")
    async def test_cancel_and_return_follow_the_order_state(self, target: Target):
        backend, facts = (
            await target.storefront(),
            need(target.storefront_facts, "storefront facts"),
        )
        request_action = getattr(backend, "request_order_action", None)
        if request_action is None:
            pytest.skip("backend has no request_order_action")
        user = need(facts.user_with_orders, "user with orders")
        session = target.shopper(user_id=user, session_id="conf-req2")
        unshipped, shipped = facts.unshipped_order_id, facts.shipped_order_id
        if unshipped:
            with pytest.raises(ValueError):
                await request_action(session, unshipped, "return", [], "too early")
            ok = await request_action(session, unshipped, "cancel", [], "changed my mind")
            assert ok.action == "cancel"
        if shipped:
            with pytest.raises(ValueError):
                await request_action(session, shipped, "cancel", [], "too late")
            order = await backend.get_order(session, shipped)
            assert order is not None
            with pytest.raises(ValueError):
                await request_action(session, shipped, "return", [facts.unknown_id], "not in it")
            ok = await request_action(
                session, shipped, "return", [order.items[0].product_id], "size"
            )
            assert ok.item_ids == [order.items[0].product_id]
        if not unshipped and not shipped:
            pytest.skip("target has no order in a known state")

    @spec("HS-S-05")
    async def test_reset_empties_the_cart_and_a_later_add_starts_fresh(self, target: Target):
        backend, facts = (
            await target.storefront(),
            need(target.storefront_facts, "storefront facts"),
        )
        reset = getattr(backend, "reset_session", None)
        if reset is None:
            pytest.skip("backend has no reset_session")
        session = target.shopper(session_id="conf-reset")
        await backend.add_to_cart(session, facts.plain_product_id, 2)
        reset(session.session_id)
        assert (await backend.get_cart(session)).items == []
        cart = await backend.add_to_cart(session, facts.plain_product_id, 1)
        assert [(i.product_id, i.quantity) for i in cart.items] == [(facts.plain_product_id, 1)]

    @spec("HS-S-01")
    async def test_unknown_id_add_raises_unavailable(self, target: Target):
        backend, facts = (
            await target.storefront(),
            need(target.storefront_facts, "storefront facts"),
        )
        session = target.shopper(session_id="conf-hs1")
        with pytest.raises(Unavailable):
            await backend.add_to_cart(session, facts.unknown_id, 1)
        assert (await backend.get_cart(session)).items == []

    @spec("HS-S-02")
    async def test_family_add_raises_unavailable_naming_variants(self, target: Target):
        backend, facts = (
            await target.storefront(),
            need(target.storefront_facts, "storefront facts"),
        )
        family = need(facts.family_id, "family")
        session = target.shopper(session_id="conf-hs2")
        with pytest.raises(Unavailable) as raised:
            await backend.add_to_cart(session, family, 1)
        assert need(facts.variant_id, "variant") in str(raised.value)
        assert (await backend.get_cart(session)).items == []

    @spec("HS-S-03")
    async def test_quantity_under_one_never_stored(self, target: Target):
        backend, facts = (
            await target.storefront(),
            need(target.storefront_facts, "storefront facts"),
        )
        session = target.shopper(session_id="conf-hs3")
        await backend.add_to_cart(session, facts.plain_product_id, 1)
        for bad in (0, -1):
            try:
                await backend.update_cart_item(session, facts.plain_product_id, bad)
            except Exception:  # noqa: BLE001 - a refusal of any kind is acceptable here
                pass
            cart = await backend.get_cart(session)
            assert all(i.quantity >= 1 for i in cart.items)

    @spec("HS-S-04")
    async def test_empty_cart_handoff_has_no_url(self, target: Target):
        backend = await target.storefront()
        session = target.shopper(session_id="conf-hs4")
        cart = await backend.get_cart(session)
        try:
            handoffs = await backend.checkout_handoff(session, cart)
        except Exception:  # noqa: BLE001
            return
        assert handoffs == []
