"""The pytest plugin: the ``spec`` marker, ``known_gaps`` as strict xfails, and a results
file per statement and target.

A test marked ``@spec("BE-S-01", ...)`` inside a class with a ``target_name`` attribute
records its outcome into the results file (``--conformance-results``, default
``conformance-results.json`` under the pytest root) at session end.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import pytest

_records: dict[str, dict[str, dict]] = defaultdict(
    lambda: defaultdict(
        lambda: {"passed": 0, "failed": 0, "skipped": 0, "known_gap": 0, "tests": []}
    )
)
_touched = False


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--conformance-results",
        default=None,
        help="where to write per-statement outcomes (default: conformance-results.json)",
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "spec(*ids): the conformance spec statements a test pins")


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """A target class may declare ``known_gaps = {"BE-M-02": "why"}``: the statements it
    is known not to meet yet. Those tests are strict xfails, so the suite stays green while
    the gap is open and turns red the moment the gap closes, asking to be removed."""
    for item in items:
        marker = item.get_closest_marker("spec")
        gaps = getattr(item.cls, "known_gaps", None) if item.cls else None
        if marker is None or not gaps:
            continue
        for sid in marker.args:
            if sid in gaps:
                item.add_marker(
                    pytest.mark.xfail(reason=f"known gap {sid}: {gaps[sid]}", strict=True)
                )
                break


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo):
    outcome = yield
    report = outcome.get_result()
    if report.when != "call" and not (report.when == "setup" and report.skipped):
        return
    marker = item.get_closest_marker("spec")
    if marker is None:
        return
    target = getattr(item.cls, "target_name", None) if item.cls else None
    if not target:
        return
    global _touched
    _touched = True
    if hasattr(report, "wasxfail"):
        result = "known_gap" if report.skipped else "failed"  # a strict xpass is a failure
    else:
        result = "failed" if report.failed else "skipped" if report.skipped else "passed"
    for sid in marker.args:
        entry = _records[target][sid]
        entry[result] += 1
        entry["tests"].append({"test": item.name, "outcome": result})


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    if not _touched:
        return
    option = session.config.getoption("--conformance-results")
    path = Path(option) if option else Path(session.config.rootpath) / "conformance-results.json"
    existing = json.loads(path.read_text()) if path.exists() else {}
    for target, specs in _records.items():
        existing[target] = {sid: dict(entry) for sid, entry in specs.items()}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(existing, indent=1, sort_keys=True))
