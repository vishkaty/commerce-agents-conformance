PY := .venv/bin/python
UPSTREAM ?= /tmp/commerce-agents

setup:            ## venv with the package, its reference-implementation dependencies, and ruff
	test -d .venv || python3 -m venv .venv
	$(PY) -m pip install -q --upgrade pip
	$(PY) -m pip install -q -e ".[dev,examples]"

upstream:         ## a checkout of the reference implementation at the pinned commit (for the example target)
	test -d $(UPSTREAM) || git clone -q https://github.com/anthropics/commerce-agents.git $(UPSTREAM)
	git -C $(UPSTREAM) checkout -q fd4d59224ab96b43c6dc6888207c67b3bd5a24cf

test: upstream    ## unit tests plus the example target, then the report and the contract
	rm -f conformance-results.json
	COMMERCE_AGENTS=$(UPSTREAM) PYTHONPATH=$(UPSTREAM)/examples $(PY) -m pytest -q -p no:cacheprovider
	$(PY) -m commerce_conformance.report --out docs/CONFORMANCE-retail-mock.md
	$(PY) -m commerce_conformance.contract --upstream $(UPSTREAM) --test-dir examples --out docs/CONTRACT.md

lint:
	$(PY) -m ruff check . && $(PY) -m ruff format --check .

.PHONY: setup upstream test lint
