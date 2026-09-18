"""The pytest plugin records outcomes per statement and target, turns declared gaps into
strict xfails, and the report renders what it recorded."""

from __future__ import annotations

import json

import pytest

from commerce_conformance.report import build, load

pytest_plugins = ["pytester"]

TARGET_FILE = """
import pytest
from commerce_conformance.facts import spec

class TestOne:
    target_name = "demo"
    known_gaps = {"BE-S-02": "not yet"}

    @spec("BE-S-01")
    def test_passes(self):
        assert True

    @spec("BE-S-02")
    def test_declared_gap_fails(self):
        assert False

    @spec("BE-S-03")
    def test_skips(self):
        pytest.skip("no fact")

    @spec("BE-S-04")
    def test_fails(self):
        assert False
"""


def test_outcomes_are_recorded_and_a_closed_gap_turns_red(pytester: pytest.Pytester):
    pytester.makepyfile(test_target=TARGET_FILE)
    result = pytester.runpytest("-p", "no:cacheprovider")
    result.assert_outcomes(passed=1, failed=1, skipped=1, xfailed=1)
    recorded = json.loads((pytester.path / "conformance-results.json").read_text())["demo"]
    assert recorded["BE-S-01"]["passed"] == 1
    assert recorded["BE-S-02"]["known_gap"] == 1
    assert recorded["BE-S-03"]["skipped"] == 1
    assert recorded["BE-S-04"]["failed"] == 1
    # The gap closes: the strict xfail fails the run, asking for the declaration to go.
    closed = TARGET_FILE.replace(
        'assert False\n\n    @spec("BE-S-03")', 'assert True\n\n    @spec("BE-S-03")'
    )
    pytester.makepyfile(test_target=closed)
    result = pytester.runpytest("-p", "no:cacheprovider")
    result.assert_outcomes(passed=1, failed=2, skipped=1)


def test_report_renders_per_target(pytester: pytest.Pytester):
    pytester.makepyfile(test_target=TARGET_FILE)
    pytester.runpytest("-p", "no:cacheprovider", "--conformance-results", "r.json")
    from commerce_conformance import spec_path

    spec, results = load(spec_path(), pytester.path / "r.json")
    text = build(spec, results)
    assert "| BE-S-01 |" in text and "| pass |" in text
    assert "known gap BE-S-02 (strict xfail): test_declared_gap_fails" in text
    assert "FAIL BE-S-04: test_fails" in text
    assert "skipped (no fact): BE-S-03" in text
