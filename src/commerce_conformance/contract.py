"""Generate the interface contract: the two backend classes a merchant implements, method
by method, from the installed commerce-agents packages (signatures and docstrings), joined
with the spec statements that pin each method and the tests that exercise it.

    commerce-conformance-contract [--out CONTRACT.md] [--upstream PATH] [--test-dir DIR]...

``--upstream`` is a checkout of anthropics/commerce-agents whose test suites are counted;
``--test-dir`` names a target's own test directories. Nothing here is typed by hand."""

from __future__ import annotations

import argparse
import ast
import inspect
import re
import sys
import textwrap
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

import yaml
from merchant_agent import types as merchant_types
from merchant_agent.backend import MerchantBackend
from shopping_agent import types as shopping_types
from shopping_agent.backend import StorefrontBackend

from commerce_conformance import spec_path

UPSTREAM_TEST_SUBDIRS = [
    "shopping-agent/core/tests",
    "merchant-agent/core/tests",
    "commerce-common/tests",
    "tests",
    "examples/demo_common/tests",
    "examples/retail/api/tests",
]

SHOPPING_TYPES = [
    "ShoppingSessionContext", "PageContext", "SearchFilters", "Product", "ProductDetails",
    "Cart", "CartItem", "CheckoutHandoff", "UserPreferences", "Order", "OrderItem",
    "OrderStatus", "Policy", "Disclosure", "DisclosureRow", "FulfillmentOption",
]  # fmt: skip
MERCHANT_TYPES = [
    "MerchantSessionContext", "ListingFilters", "Listing", "ListingDetails",
    "BusinessSnapshot", "AlertCounts", "MetricSeries", "MetricPoint", "Campaign",
    "InventoryAlert", "OrderIssue", "PricingContext", "PriceUpdateItem",
    "InventoryActionItem", "PromotionDraft", "CampaignDraft", "StagedChange", "ChangeItem",
    "ChangeKind", "ChangeStatus", "ActorKind", "AnalysisTable", "DataLimitation",
]  # fmt: skip


def cell(text: str) -> str:
    """Markdown table cells cannot hold a bare pipe; union types are full of them."""
    return text.replace("|", "\\|")


def tests_using(dirs: list[Path], method: str) -> list[str]:
    """Test functions whose body mentions the method (as a call, a tool name or a string)."""
    pattern = re.compile(rf"\b{re.escape(method)}\b")
    found: list[str] = []
    for directory in dirs:
        if not directory.is_dir():
            continue
        for path in sorted(directory.rglob("test_*.py")) + sorted(directory.glob("contract.py")):
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source)
            for node in ast.walk(tree):
                is_test = isinstance(node, ast.AsyncFunctionDef | ast.FunctionDef)
                if is_test and node.name.startswith("test_"):
                    segment = ast.get_source_segment(source, node) or ""
                    if pattern.search(segment):
                        found.append(f"{path.name}::{node.name}")
    return found


def method_rows(cls: type) -> list[dict[str, Any]]:
    abstract = set(getattr(cls, "__abstractmethods__", set()))
    rows = []
    for name, member in inspect.getmembers(cls, predicate=inspect.isfunction):
        if name.startswith("_"):
            continue
        signature = inspect.signature(member)
        params = [
            f"{p.name}: {inspect.formatannotation(p.annotation)}"
            + (f" = {p.default!r}" if p.default is not inspect.Parameter.empty else "")
            for p in list(signature.parameters.values())[1:]
        ]
        returns = inspect.formatannotation(signature.return_annotation)
        doc = textwrap.dedent(member.__doc__ or "").strip().replace("\n", " ")
        rows.append(
            {
                "name": name,
                "kind": "abstract" if name in abstract else "optional (has a default)",
                "params": params,
                "returns": returns,
                "doc": re.sub(r"\s+", " ", doc),
                "line": inspect.getsourcelines(member)[1],
            }
        )
    order = [n for n in cls.__dict__ if n in {r["name"] for r in rows}]  # declaration order
    return sorted(rows, key=lambda r: order.index(r["name"]))


def type_rows(module: Any, names: list[str]) -> list[tuple[str, str]]:
    rows = []
    for name in names:
        model = getattr(module, name)
        if hasattr(model, "model_fields"):
            fields = []
            for field_name, field in model.model_fields.items():
                annotation = inspect.formatannotation(field.annotation)
                default = "" if field.is_required() else " (optional)"
                fields.append(f"`{field_name}: {annotation}`{default}")
            rows.append((name, cell("; ".join(fields))))
        else:  # an enum
            rows.append((name, ", ".join(f"`{m.value}`" for m in model)))
    return rows


def spec_index(spec_file: Path) -> tuple[dict, dict[str, list[dict]]]:
    spec = yaml.safe_load(spec_file.read_text())
    by_method: dict[str, list[dict]] = defaultdict(list)
    for area in spec["areas"]:
        for statement in area["statements"]:
            for method in statement.get("methods") or []:
                by_method[method].append({**statement, "area": area["id"]})
    return spec, by_method


def render_interface(
    title: str, cls: type, source: str, by_method: dict, upstream_dirs: list, target_dirs: list
) -> list[str]:
    first_line = cls.__doc__.strip().splitlines()[0] if cls.__doc__ else ""
    lines = [f"## {title}", "", f"Source: `{source}` (upstream). {first_line}", ""]
    rows = method_rows(cls)
    lines += [
        "| Method | Kind | Contract (upstream docstring) | Spec | Upstream tests | Target "
        "tests | E2E |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        statements = by_method.get(row["name"], [])
        contract_ids = [s["id"] for s in statements if s["area"] not in {"E2E"}]
        e2e_ids = [s["id"] for s in statements if s["area"] == "E2E"]
        upstream = tests_using(upstream_dirs, row["name"])
        lab = tests_using(target_dirs, row["name"])
        signature = cell(f"`{row['name']}({', '.join(row['params'])}) -> {row['returns']}`")
        lines.append(
            "| "
            + " | ".join(
                [
                    signature,
                    row["kind"],
                    cell(row["doc"]) or "—",
                    ", ".join(contract_ids) or "**none**",
                    str(len(upstream)),
                    str(len(lab)),
                    ", ".join(e2e_ids) or "—",
                ]
            )
            + " |"
        )
    lines.append("")
    lines.append("<details><summary>Which tests, per method</summary>")
    lines.append("")
    for row in rows:
        upstream = tests_using(upstream_dirs, row["name"])
        lab = tests_using(target_dirs, row["name"])
        up_names = ", ".join(f"`{t}`" for t in upstream) or "none"
        lab_names = ", ".join(f"`{t}`" for t in lab) or "none"
        lines.append(f"**{row['name']}** — upstream: {up_names}; target: {lab_names}")
        lines.append("")
    lines.append("</details>")
    lines.append("")
    return lines


def build(spec_file: Path, upstream: Path | None, target_dirs: list[Path]) -> str:
    spec, by_method = spec_index(spec_file)
    upstream_dirs = [upstream / sub for sub in UPSTREAM_TEST_SUBDIRS] if upstream else []
    lines = [
        "# Interface contract: what a merchant implements",
        "",
        f"Generated {date.today().isoformat()} by `commerce-conformance-contract` from the "
        "installed commerce-agents packages, joined with the conformance spec "
        f"(version {spec['version']}). The *Contract* column is the upstream docstring verbatim; "
        "*Spec* lists the statements that pin the method (BE = backend contract, EX = executor "
        "behaviour over the method, HS = proposed hardening); *Upstream tests* and *Target "
        "tests* count test functions whose body names the method; *E2E* lists the end-to-end "
        "flows in the spec that cross it. A method with **none** in Spec is an open item.",
        "",
        "The two backend classes are the integration: a merchant subclasses each and implements "
        "the abstract methods over their own platform. Everything else (executors, gates, "
        "fencing, runtimes, UI enrichment) is upstream code the merchant configures but does "
        "not write.",
        "",
    ]
    lines += render_interface(
        "StorefrontBackend (shopping agent)",
        StorefrontBackend,
        "shopping-agent/core/shopping_agent/backend.py",
        by_method,
        upstream_dirs,
        target_dirs,
    )
    lines += render_interface(
        "MerchantBackend (merchant agent)",
        MerchantBackend,
        "merchant-agent/core/merchant_agent/backend.py",
        by_method,
        upstream_dirs,
        target_dirs,
    )
    lines += ["## Exceptions a backend raises", ""]
    lines += ["| Exception | When | Effect on the model |", "|---|---|---|"]
    lines += [
        "| `shopping_agent.backend.Unavailable` | a product or variant exists but cannot be "
        "bought now | relayed, ids only; nothing written |",
        "| `shopping_agent.backend.NotOffered` | this store does not provide the thing for the "
        'item in hand | "not something this store offers" |',
        "| `merchant_agent.changes.GuardrailViolation` | a staged change breaks a config "
        "guardrail | the violations, nothing staged |",
        "| `merchant_agent.changes.ChangeNotApplicable` | a system the deployment lacks, or a "
        "change that is not staged | relayed as such |",
        '| any other exception | a failing system | "temporarily unavailable", logged by the '
        "executor |",
        "",
    ]
    lines += [
        "## Types exchanged",
        "",
        "Pydantic models from `shopping_agent/types.py` and `merchant_agent/types.py`; a "
        "field without *(optional)* is required.",
        "",
    ]
    lines += ["### Shopping", "", "| Type | Fields |", "|---|---|"]
    lines += [f"| `{n}` | {f} |" for n, f in type_rows(shopping_types, SHOPPING_TYPES)]
    lines += ["", "### Merchant", "", "| Type | Fields |", "|---|---|"]
    lines += [f"| `{n}` | {f} |" for n, f in type_rows(merchant_types, MERCHANT_TYPES)]
    lines += ["", "## Statements without a method", ""]
    loose = [
        f"- {s['id']} ({area['id']}): {s['text']}"
        for area in spec["areas"]
        for s in area["statements"]
        if not s.get("methods")
    ]
    lines += loose or ["- none"]
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=Path("CONTRACT.md"))
    parser.add_argument("--spec", type=Path, default=spec_path())
    parser.add_argument("--upstream", type=Path, default=None)
    parser.add_argument("--test-dir", type=Path, action="append", default=[])
    args = parser.parse_args(argv)
    args.out.write_text(build(args.spec, args.upstream, args.test_dir))
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
