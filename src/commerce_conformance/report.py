"""Join spec.yaml with recorded outcomes into a Markdown report.

    commerce-conformance-report [--results conformance-results.json] [--out CONFORMANCE.md]

The pytest plugin writes the results file:
{"<target>": {"<spec id>": {"passed": n, "failed": n, "skipped": n, "known_gap": n,
              "tests": [...]}}}
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

import yaml

from commerce_conformance import spec_path


def load(spec_file: Path, results_file: Path) -> tuple[dict, dict]:
    spec = yaml.safe_load(spec_file.read_text())
    results = json.loads(results_file.read_text()) if results_file.exists() else {}
    return spec, results


def cell(entry: dict | None) -> str:
    if not entry:
        return "—"
    if entry["failed"]:
        return f"FAIL ({entry['failed']})"
    if entry.get("known_gap"):
        return "known gap"
    if entry["passed"]:
        return "pass"
    if entry["skipped"]:
        return "skip"
    return "—"


def build(spec: dict, results: dict) -> str:
    targets = sorted(results)
    lines = [
        "# Conformance report",
        "",
        f"Generated {date.today().isoformat()} by `commerce-conformance-report`. "
        f"Spec version {spec['version']}; "
        f"{sum(len(a['statements']) for a in spec['areas'])} statements. "
        "Columns are targets: a cell is pass, FAIL, known gap (a strict xfail the target "
        "declares), skip (the target lacks the fact the statement needs), or — (no test). "
        "Statements marked upstream are pinned by the reference implementation's own suite "
        "and listed for completeness.",
        "",
    ]
    mapped = unmapped = 0
    for area in spec["areas"]:
        lines += [
            f"## {area['id']}: {area['title']}",
            "",
            "| Id | Statement | " + " | ".join(targets) + " |",
            "|---|---|" + "---|" * len(targets),
        ]
        for statement in area["statements"]:
            sid = statement["id"]
            row = [sid, statement["text"]]
            has_test = any(sid in results.get(t, {}) for t in targets)
            upstream = statement.get("upstream_tests")
            if has_test or upstream:
                mapped += 1
            else:
                unmapped += 1
            for target in targets:
                row.append(
                    cell(results.get(target, {}).get(sid))
                    if has_test
                    else (f"upstream: {upstream}" if upstream else "—")
                )
            lines.append("| " + " | ".join(row) + " |")
        lines.append("")
    total = mapped + unmapped
    lines.insert(
        4,
        f"**Spec mapping: {mapped}/{total} statements have a test "
        f"({100 * mapped // max(total, 1)}%).**",
    )
    lines.insert(5, "")
    lines += ["## Failures, known gaps and skips by target", ""]
    for target in targets:
        fails = [(sid, e) for sid, e in results[target].items() if e["failed"]]
        skips = [
            sid
            for sid, e in results[target].items()
            if e["skipped"] and not e["passed"] and not e["failed"]
        ]
        gaps = [(sid, e) for sid, e in results[target].items() if e.get("known_gap")]
        lines += [f"### {target}", ""]
        if fails:
            for sid, entry in fails:
                names = ", ".join(t["test"] for t in entry["tests"] if t["outcome"] == "failed")
                lines.append(f"- FAIL {sid}: {names}")
        else:
            lines.append("- no failures")
        for sid, entry in gaps:
            names = ", ".join(t["test"] for t in entry["tests"] if t["outcome"] == "known_gap")
            lines.append(f"- known gap {sid} (strict xfail): {names}")
        if skips:
            lines.append(f"- skipped (no fact): {', '.join(skips)}")
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--results", type=Path, default=Path("conformance-results.json"))
    parser.add_argument("--spec", type=Path, default=spec_path())
    parser.add_argument("--out", type=Path, default=Path("CONFORMANCE.md"))
    args = parser.parse_args(argv)
    spec, results = load(args.spec, args.results)
    args.out.write_text(build(spec, results))
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
