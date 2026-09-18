"""Conformance suite for Claude Commerce Agents backends and executors.

A target (`facts.Target`) names a backend implementation and the fixture facts the
statements need; the suites (`storefront_suite`, `merchant_suite`, `executor_suite`)
are pytest mixins a target file subclasses. Every test carries `@spec(...)` ids from
`spec.yaml`; the pytest plugin records outcomes per statement and target, and
`commerce-conformance-report` renders them.
"""

from importlib.resources import files
from pathlib import Path

__version__ = "0.1.0"


def spec_path() -> Path:
    """The packaged spec.yaml."""
    return Path(str(files("commerce_conformance") / "spec.yaml"))
