# Conformance report

Generated 2026-09-18 by `commerce-conformance-report`. Spec version 2026-09-09; 137 statements. Columns are targets: a cell is pass, FAIL, known gap (a strict xfail the target declares), skip (the target lacks the fact the statement needs), or — (no test). Statements marked upstream are pinned by the reference implementation's own suite and listed for completeness.

**Spec mapping: 127/137 statements have a test (92%).**

## BE-S: StorefrontBackend contract

| Id | Statement | demo | upstream-retail-mock |
|---|---|---|---|
| BE-S-01 | search_products returns at most `limit` results, best first, and an empty list when nothing matches. | pass | pass |
| BE-S-02 | search_products returns a family as one result; its variants are never results of their own. | FAIL (1) | pass |
| BE-S-03 | get_product_details returns the full record for a known id and None for an unknown id. | skip | pass |
| BE-S-04 | A family's details carry every purchasable variant with option_values and variant_of; a variant's id returns that variant. | FAIL (3) | pass |
| BE-S-05 | A family's price is its lowest in-stock variant's and it is in stock while any variant is. | — | pass |
| BE-S-06 | get_cart returns an empty cart for a session that has added nothing. | — | pass |
| BE-S-07 | add_to_cart adds a purchasable id and returns the whole cart; lines belong to the session that added them. | — | pass |
| BE-S-08 | add_to_cart of a variant that exists but cannot be bought raises Unavailable naming ids only, and writes nothing. | — | pass |
| BE-S-09 | update_cart_item sets a held line to the quantity; a product the cart does not hold leaves the cart as it is. | — | pass |
| BE-S-10 | remove_from_cart removes a held line; a product the cart does not hold leaves the cart as it is. | — | pass |
| BE-S-11 | get_preferences returns a profile for every session, a guest included. | — | pass |
| BE-S-12 | get_orders returns the customer's own orders newest first, at most `limit`; a customer without orders gets an empty list. | — | pass |
| BE-S-13 | get_order returns None for an unknown id. | — | pass |
| BE-S-14 | search_policies returns the passages matching the query and an empty list when none do. | — | pass |
| BE-S-15 | get_fulfillment_options returns options for known ids and skips ids the catalog does not know. | — | pass |
| BE-S-16 | checkout_handoff returns an empty list by default, or https URLs the host renders; no backend method places an order. | — | pass |
| BE-S-17 | search_products honours filters; every result respects max_price and sort=price_asc yields non-decreasing prices. | — | pass |
| BE-S-18 | Odd input (empty, very long, unicode, regex or path characters) never raises; search returns a list and details returns None. | — | pass |
| BE-S-19 | A second add of the same id adds to the existing line; the cart holds one line per id. | — | pass |
| BE-S-20 | A cart line's title and price match the product record and the cart's currency matches the product's. | — | pass |
| BE-S-21 | A family record is consistent; options are non-empty, every variant sets exactly the family's options with listed values, and no two variants share the same values. | — | pass |
| BE-S-22 | get_order returns None for an order that belongs to another customer. | — | pass |
| BE-S-23 | Every order carries an id, a status, a placed_at, a non-negative total and items with quantity of at least one. | — | pass |
| BE-S-24 | search_policies matches regardless of case and returns the same passages for the same query. | — | pass |
| BE-S-25 | Concurrent adds of the same id from one session both land; the backend applies its rules atomically. | — | pass |
| BE-S-26 | get_disclosure returns None for a product without one (the default) or a Disclosure whose product_id is the product asked for. | — | pass |
| BE-S-27 | get_account_context returns None (the default) or a small JSON-serialisable dict, since it rides on every request. | — | pass |
| BE-S-28 | search_policies and get_fulfillment_options never raise on odd input; they return a list. | — | pass |

## BE-M: MerchantBackend contract

| Id | Statement | demo | upstream-retail-mock |
|---|---|---|---|
| BE-M-01 | get_business_snapshot returns a period with sales and orders; a figure the store cannot supply is None, never a stand-in zero. | — | pass |
| BE-M-02 | query_metrics returns dated points for a known metric; a segment or metric the store cannot supply comes back with no points and a note. | — | known gap |
| BE-M-03 | search_listings returns families, never their variants, and honours the filters it is given. | — | pass |
| BE-M-04 | get_listing returns the full record for a known id, its variants for a family, and None for an unknown id. | — | pass |
| BE-M-05 | get_inventory_alerts returns alerts that name purchasable listings with their stock; an empty list means nothing is flagged. | — | pass |
| BE-M-06 | get_order_issues returns a list of open exceptions, possibly empty. | — | pass |
| BE-M-07 | get_pricing_context returns context for a known listing or variant, per-variant contexts for a family, and None for an unknown id. | — | pass |
| BE-M-08 | Every stage_* method records a proposal stamped with the operator without touching live state. | — | pass |
| BE-M-09 | A price update or a restock that names a family is refused; they name a variant. | — | pass |
| BE-M-10 | get_pending_changes lists exactly the changes staged but not yet applied or discarded. | — | pass |
| BE-M-11 | apply_change performs the platform write for a staged change, marks it applied by the operator, and the next read reflects it. | — | pass |
| BE-M-12 | apply_change refuses an unknown id and a change that is not currently staged. | — | pass |
| BE-M-13 | discard_change marks a staged change discarded and records who discarded it and on whose initiative. | — | pass |
| BE-M-14 | A price move beyond max_price_delta_pct is refused at staging with a GuardrailViolation and nothing is staged. | — | pass |
| BE-M-15 | A promotion that names a family expands to one line per variant. | — | pass |
| BE-M-16 | A campaign budget beyond max_campaign_budget is refused at staging. | — | pass |
| BE-M-17 | A pause or activation stages a status item and applying it changes the listing's status. | — | pass |
| BE-M-18 | query_metrics for a metric the store does not have returns no points and a note, never another metric's series. | — | known gap |
| BE-M-19 | A non-positive price is refused, and a price under the listing's min_price is refused by the backend's own rule. | — | pass |
| BE-M-20 | A change with more than max_items_per_change items is refused and nothing is staged. | — | pass |
| BE-M-21 | A promotion discount beyond max_promotion_discount_pct is refused and nothing is staged. | — | pass |
| BE-M-22 | A listing update naming a protected field (listing_id, currency) or a blocked one (price, stock) is refused. | — | pass |
| BE-M-23 | apply and discard stamp the operator of the session that performed them, not the one that staged. | — | pass |
| BE-M-24 | get_listing on a variant's id returns that variant with variant_of set and no variants of its own. | — | pass |
| BE-M-25 | search_listings honours the status filter and sort=stock_asc yields non-decreasing stock. | — | pass |
| BE-M-26 | When the platform write fails, apply_change raises and the change stays staged. | — | skip |
| BE-M-27 | stage_campaign naming a campaign_id the store does not have is refused. | — | known gap |
| BE-M-28 | get_campaign_performance returns every campaign, or only the one named; an unknown campaign_id yields an empty list; spend and revenue are None when a channel does not report them. | — | pass |
| BE-M-29 | Analysis is either unsupported (both return None) or a SELECT returns a capped AnalysisTable and anything else is refused. | — | pass |
| BE-M-30 | get_merchant_context returns None or a small dict whose limitations entries validate as DataLimitation. | — | pass |
| BE-M-31 | Odd input (empty, very long, unicode, regex or path characters) never raises; search returns a list, listing and pricing reads return None. | — | pass |
| BE-M-32 | apply_change for a listing the platform no longer has raises and the change stays staged. | — | skip |

## EX-S: Shopping executor over any backend

| Id | Statement | demo | upstream-retail-mock |
|---|---|---|---|
| EX-S-01 | Search results reach the model fenced under the storefront label and enter the session's provenance. | — | pass |
| EX-S-02 | A cart write for an id no tool returned this session is held by the provenance gate and nothing is written. | — | pass |
| EX-S-03 | Adding a family with options still to choose is held by the options gate, which points at its variants. | — | pass |
| EX-S-04 | A quantity above max_quantity_per_item is reduced to the cap and the cap is reported. | — | pass |
| EX-S-05 | Third-party text carrying instructions, forged turn markers or fence copies is sanitized before the model reads it. | — | pass |
| EX-S-06 | checkout renders the cart on a card; a handoff URL rides on the card payload and never in the model's result. | — | pass |
| EX-S-07 | A presentation call naming an id the server never returned is refused; known ids are joined from server records. | — | pass |
| EX-S-08 | The executor refuses a tool name the deployment config does not build. | — | pass |
| EX-S-09 | A backend exception is a soft error result, not an exception out of the executor. | — | pass |
| EX-S-10 | A line the site put in the cart outside the chat can be updated and removed; cart membership alone grants it. | — | pass |
| EX-S-11 | With the cart at max_cart_lines, a new line is refused and nothing is written. | — | pass |
| EX-S-12 | Invalid model arguments (a non-numeric or negative quantity) are a soft error naming the argument; nothing is written. | — | known gap |
| EX-S-13 | Every read tool's result is fenced under the storefront label. | — | pass |
| EX-S-14 | Items of an order the customer read this turn pass provenance, so a reorder needs no search. | — | pass |
| EX-S-15 | Extra arguments the schema does not name are ignored, not an error. | — | pass |
| EX-S-16 | Hostile text in a policy passage is sanitized before the model reads it. | — | pass |
| EX-S-17 | Hostile text in an order item's title is sanitized before the model reads it. | — | pass |
| EX-S-18 | A saved fact carrying fence markers or instructions is stored sanitized and read back fenced. | — | pass |
| EX-S-19 | A fulfillment call naming more than twenty ids is a soft error or a bounded answer, never an exception. | — | pass |
| EX-S-20 | An update above max_quantity_per_item is reduced to the cap and the cap is reported. | — | pass |
| EX-S-22 | Hostile text in a fulfillment option's label or a preference value is sanitized before the model reads it. | — | pass |
| EX-S-23 | A memory fact the model tries to save with an over-long or hostile value is truncated or refused, never stored raw. | — | pass |
| EX-S-24 | A cart at max_cart_lines renders on the checkout card whole and the model's result stays within max_fenced_chars. | — | skip |
| EX-S-21 | When checkout_handoff refuses a stale cart, checkout reports the refusal to the model naming the line, not an outage. | — | known gap |

## EX-M: Merchant executor over any backend

| Id | Statement | demo | upstream-retail-mock |
|---|---|---|---|
| EX-M-01 | A stage_* call naming a listing no tool returned this session is held by the provenance gate. | — | pass |
| EX-M-02 | With require_host_approval on, apply_change for a change the host has not marked approved is held by the approval gate. | — | pass |
| EX-M-03 | apply_change for a change the host marked approved applies it; a second apply reports it already applied. | — | pass |
| EX-M-04 | A guardrail violation at staging is reported to the model and nothing is staged. | — | pass |
| EX-M-05 | Listing results reach the model fenced under the merchant label and enter provenance. | — | pass |
| EX-M-06 | A content edit needs the full record read this session in addition to search provenance. | — | pass |
| EX-M-07 | A price update naming a family is held by the options gate before it reaches the backend. | — | pass |
| EX-M-08 | A discard the assistant drives is recorded as the agent's; one the host marked as its own action is recorded as the operator's. | — | pass |
| EX-M-09 | A change staged outside this session is held by provenance until get_pending_changes lists it, then by approval. | — | pass |
| EX-M-10 | A listing field over max_listing_field_chars is refused with the limit named, never truncated into a live listing. | — | pass |
| EX-M-11 | Hostile listing text in merchant results is sanitized before the model reads it. | — | pass |

## HS: Hardening beyond the written contract (proposals)

| Id | Statement | demo | upstream-retail-mock |
|---|---|---|---|
| HS-S-01 | add_to_cart of an id the catalog does not know raises Unavailable, not an arbitrary exception, and writes nothing. | — | known gap |
| HS-S-02 | add_to_cart of a family raises Unavailable naming its variants and writes nothing. | — | known gap |
| HS-S-03 | update_cart_item with a quantity under one is refused or removes the line; no line is ever stored below one. | — | known gap |
| HS-S-04 | checkout_handoff on an empty cart yields no URL. | — | pass |
| HS-S-05 | After the host resets a session, its cart is empty and a later add starts a fresh cart. | — | pass |
| HS-S-06 | Model-authored text on a card (a pick's reason) reaches the host without fence markers or invisible characters. | — | known gap |
| HS-S-07 | checkout_handoff re-validates the cart; a line that can no longer be bought raises Unavailable naming it and no payment URL is produced. | — | known gap |
| HS-S-08 | request_order_action records a cancellation, return or problem for one of the customer's own orders as a request with a status; nothing is written to the platform, and another customer's or an unknown order is refused. | — | skip |
| HS-S-09 | A cancellation is refused once the order has shipped and a return before it has; items named must belong to the order. | — | skip |
| HS-M-01 | A change is scoped to the merchant that staged it; a session for another merchant neither lists nor applies nor discards it. | — | known gap |
| HS-M-02 | A restock without a quantity, or with zero, is refused rather than staged as a no-op. | — | known gap |
| HS-M-03 | Concurrent applies of one change apply it once; the other attempt is refused. | — | pass |
| HS-M-04 | A promotion whose end precedes its start is refused. | — | known gap |
| HS-M-05 | A multi-item apply that fails part way stays staged, and a retry once the platform recovers converges every item to its staged after-value. | — | skip |
| HS-M-06 | A promotion that already ended is refused. | — | known gap |
| HS-M-07 | A price with more than two decimals is refused or rounded; it is never applied as written. | — | known gap |
| HS-M-08 | A staged change survives a restart; a new backend over the same store still lists it and can apply it. | — | skip |
| HS-M-09 | Two backend instances over the same store applying one change apply it once; the other attempt is refused. | — | skip |
| HS-M-10 | An apply that dies after the platform write and before the stamp is completed by a retry without writing again. | — | skip |
| HS-M-12 | A staged change is flagged when a pending change touches the same target and field, and a price or status change is refused at apply when the platform value moved since staging. | — | known gap |
| HS-M-13 | An applied price, stock or content change can be undone; the inverse is staged like any change and applying it restores the values; a promotion or campaign cannot. | — | skip |
| HS-M-14 | A staged change can be scheduled; it applies when its time has come, stamped with the scheduling operator, and not before. | — | skip |
| HS-M-15 | A promotion that would take a listing under its min_price is refused at staging. | — | known gap |
| EX-M-12 | A change with max_items_per_change items previews every line on the card and the fenced result stays within max_fenced_chars. | — | pass |
| BE-M-33 | A listing update with odd field values (empty, very long, unicode, fence markers) never raises an unhandled error; it is refused or staged (the executor sanitizes before the backend sees it). | — | pass |
| HS-M-11 | A shopper's open request is an order issue for the merchant; resolving it records the operator's decision, closes the issue, and an approved cancellation is written to the platform on the merchant's side. | — | skip |

## RT: Runtime rules pinned by upstream's own suite (informational)

| Id | Statement | demo | upstream-retail-mock |
|---|---|---|---|
| RT-01 | Grounding gates force a read on a turn's first iteration for terms, order and unseen-id messages. | upstream: tests/test_turn_loop.py | upstream: tests/test_turn_loop.py |
| RT-02 | After max_tool_iterations the Messages API runtime forces a round without tools; past compact_history_above_tokens it clears the oldest tool results. | upstream: tests/test_turn_loop.py | upstream: tests/test_turn_loop.py |
| RT-03 | Memory extraction reads only the last exchange's user and assistant text and never tool results. | upstream: commerce-common/tests/test_memory_runtime.py | upstream: commerce-common/tests/test_memory_runtime.py |
| RT-04 | The static prompt and tool list are byte-identical across requests; per-request data sits after the cache breakpoint. | upstream: tests/test_turn_loop.py, tests/test_system_switches.py | upstream: tests/test_turn_loop.py, tests/test_system_switches.py |

## HOST: Host rules

| Id | Statement | demo | upstream-retail-mock |
|---|---|---|---|
| HOST-01 | No route reads identity from the request; a session id is the only credential after session start. | upstream: examples/demo_common/tests/contract.py | upstream: examples/demo_common/tests/contract.py |
| HOST-02 | A preview card's approval marks the change on the host's side before the executor runs, and the mark does not outlive the click. | upstream: examples/demo_common/tests/contract.py | upstream: examples/demo_common/tests/contract.py |

## E2E: End-to-end flows the Medusa adapter pins (offline over its store host, live over Medusa and Stripe)

| Id | Statement | demo | upstream-retail-mock |
|---|---|---|---|
| E2E-01 | Shopper searches, reads, adds, and checkout hands off to a hosted payment URL; the model never sees the URL. | — | — |
| E2E-02 | A paid webhook places the order once; a replayed event and a late webhook both leave exactly one order, and the shopper's get_orders shows it. | — | — |
| E2E-03 | A merchant change approved in the portal is applied to the platform and the storefront's next read shows it. | — | — |
| E2E-04 | An order placed through the shopper flow appears in the merchant's snapshot for the day. | — | — |
| E2E-05 | A chat turn on the Agent SDK path streams tool calls, gate outcomes, UI payloads, cart updates, text and completion in order, one client per session. | — | — |
| E2E-06 | The demo's access-code gate admits shoppers to the store and only the admin code to the portal; cookies expire and tampering is refused. | — | — |
| E2E-07 | Search, details, cart writes and orders round-trip against the running store for a signed-in customer. | — | — |
| E2E-09 | On the SDK path the order-action tool is held until the order was read, then records the request; the merchant sees it as an issue and the portal resolves it. | — | — |
| E2E-10 | The webhook and the success page arriving together for one paid cart place one order; the second caller reads the first's result. | — | — |
| E2E-08 | The host completes a paid cart only when the amount Stripe collected matches the cart's total at completion; a mismatch is held for review and nothing is placed. | — | — |

## Failures, known gaps and skips by target

### demo

- FAIL BE-S-02: test_declared_gap_fails
- FAIL BE-S-04: test_fails, test_fails, test_fails
- known gap BE-S-02 (strict xfail): test_declared_gap_fails, test_declared_gap_fails
- skipped (no fact): BE-S-03

### upstream-retail-mock

- no failures
- known gap BE-M-02 (strict xfail): test_metrics_known_and_unsupported_segment
- known gap BE-M-18 (strict xfail): test_unknown_metric_has_no_points_and_a_note
- known gap BE-M-27 (strict xfail): test_editing_an_unknown_campaign_is_refused
- known gap EX-S-12 (strict xfail): test_invalid_arguments_are_soft_errors
- known gap EX-S-21 (strict xfail): test_checkout_relays_a_stale_cart_refusal
- known gap HS-M-01 (strict xfail): test_changes_are_scoped_to_their_merchant
- known gap HS-M-02 (strict xfail): test_restock_without_quantity_is_refused
- known gap HS-M-04 (strict xfail): test_promotion_ending_before_it_starts_is_refused
- known gap HS-M-06 (strict xfail): test_promotion_that_already_ended_is_refused
- known gap HS-M-07 (strict xfail): test_sub_cent_price_is_refused_or_rounded
- known gap HS-M-12 (strict xfail): test_conflicts_are_flagged_and_a_moved_price_is_refused
- known gap HS-M-15 (strict xfail): test_promotion_under_the_floor_is_refused
- known gap HS-S-01 (strict xfail): test_unknown_id_add_raises_unavailable
- known gap HS-S-02 (strict xfail): test_family_add_raises_unavailable_naming_variants
- known gap HS-S-03 (strict xfail): test_quantity_under_one_never_stored
- known gap HS-S-06 (strict xfail): test_hostile_pick_reason_does_not_reach_the_card_raw
- known gap HS-S-07 (strict xfail): test_handoff_refuses_a_line_that_became_unpurchasable
- skipped (no fact): BE-M-26, BE-M-32, EX-S-24, HS-M-05, HS-M-08, HS-M-09, HS-M-10, HS-M-11, HS-M-13, HS-M-14, HS-S-08, HS-S-09
