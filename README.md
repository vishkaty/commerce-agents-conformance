# commerce-agents-conformance

A conformance suite a merchant runs against their own backend for Anthropic's
[Claude Commerce Agents](https://github.com/anthropics/commerce-agents): 137 numbered
statements distilled from the reference implementation's contract, pytest mixins that
check a backend and the executors over it, a per-statement report, and a generated
interface contract.

The reference repository is a one-way publication: its README says it "is not
maintained and does not accept contributions", and it ships no way to check an
implementation against its `StorefrontBackend` and `MerchantBackend` contract beyond the
examples' own tests. Running the contract as tests against those examples found a dozen
departures ([the pull requests](https://github.com/anthropics/commerce-agents/pulls?q=is%3Apr+author%3Avishkaty)
record them, and a maintained fork has adopted twelve). A merchant's own adapter has no
such check at all. This package is that check.

## What a run looks like

```
$ pytest my_backend/test_conformance.py
....x..s.....                                                       [100%]
$ commerce-conformance-report
wrote CONFORMANCE.md
```

`CONFORMANCE.md` is one row per statement and one column per target: pass, FAIL, known
gap, or skip, plus the spec-mapping percentage. `docs/CONFORMANCE-retail-mock.md` is the
report for the reference retail mock; `make test` also writes `docs/CONTRACT.md`, the
interface contract generated from the installed packages, method by method, with the
statements that pin each method (CI publishes it as a build artifact).

## Install

```
pip install "commerce-agents-conformance @ git+https://github.com/vishkaty/commerce-agents-conformance"
```

The reference packages (`commerce-common`, `shopping-agent-core`, `merchant-agent-core`)
are not on PyPI; they install from the reference repository at the commit this release
was verified against (`fd4d592`, 2026-08-31). Python 3.11 or newer.

## Run it against your backend

A target is a small pytest file: a factory per backend, the facts the statements need,
and the mixins. This is the whole of it for a storefront:

```python
from commerce_conformance.facts import StorefrontFacts, Target
from commerce_conformance.storefront_suite import StorefrontConformance
from commerce_conformance.executor_suite import ShoppingExecutorConformance
import pytest

from my_store import MyStorefront, my_shopping_config


@pytest.fixture
def target() -> Target:
    return Target(
        name="my-store",
        make_storefront=lambda: MyStorefront(),  # sync or async
        shopping_config=my_shopping_config(),
        storefront_facts=StorefrontFacts(
            search_query="kettle",  # matches at least two listings
            plain_product_id="SKU-100",  # in stock, no options
            family_id="SKU-200",  # a product with options, if any
            variant_id="SKU-200-RED",
            out_of_stock_variant_id="SKU-200-BLUE",
            user_with_orders="customer-1",
            other_users_order_id="order-of-someone-else",
        ),
    )


class TestStorefront(StorefrontConformance):
    target_name = "my-store"


class TestShoppingExecutor(ShoppingExecutorConformance):
    target_name = "my-store"
    known_gaps = {"HS-S-07": "checkout does not re-validate the cart yet (ticket 42)"}
```

- A fact the target lacks skips the statements that need it, and says so.
- A statement the target is known not to meet is declared once in `known_gaps` and runs
  as a strict xfail: the suite stays green while the gap is open and turns red the day it
  closes, asking for the declaration to be removed.
- `MerchantFacts`, `MerchantConformance` and `MerchantExecutorConformance` do the same
  for the merchant side. `Target` also takes optional hooks (`make_unpurchasable`,
  `move_price_on_platform`, `break_merchant_writes`, ...) that unlock the statements about
  a platform changing under the agent; without a hook those statements skip.
- `examples/retail_mock/test_retail_mock.py` is the complete target file for the
  reference retail mock, gaps and all.

## The spec

`src/commerce_conformance/spec.yaml`: numbered, one-sentence normative statements, each
naming the backend methods or tools it is about and where it comes from in the reference
repository.

| Area | Statements | About |
|---|---|---|
| BE-S, BE-M | 61 | the `StorefrontBackend` and `MerchantBackend` contract proper |
| EX-S, EX-M | 40 | the executors over any backend: gates, provenance, caps, approval |
| HS-S, HS-M | 22 | hardening the reference does not state (fencing of backend text, contract-typed refusals, ledger scoping, price and promotion floors) |
| RT, HOST, E2E | 14 | runtime, host identity and session rules, end-to-end flows |

Statements marked `upstream_tests` are pinned by the reference's own suite and listed for
completeness. The `HS` statements are proposals; declare them as known gaps if you do not
want them.

## Develop

```
make setup      # venv, package, reference dependencies, ruff
make test       # unit tests + the retail-mock example, then the report and the contract
make lint
```

`make test` clones the reference repository to `/tmp/commerce-agents` at the pinned
commit for the example target (`UPSTREAM=` to point elsewhere).

## Status

Version 0.1.0, 2026-09-18. The suite has run against the reference retail, travel, telecom
and entertainment mocks and against a Medusa v2 adapter, offline and live. Issues and
pull requests are open here.

## License

Apache-2.0. The statements are distilled from the reference implementation's
documentation and docstrings (Apache-2.0, Anthropic PBC); see `NOTICE`.
