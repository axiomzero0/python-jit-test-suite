"""Pytest wrappers around the suite.

These let you run the suite as a regular pytest invocation, optionally
sharded with pytest-xdist::

    pytest -x -q
    pytest -x -q -k numeric
    pytest -n auto --dist loadscope
"""

from __future__ import annotations

import os

import pytest

from jit_tests.harness import Runner, StateController
from jit_tests.deterministic import generate_category, DEFAULT_COUNTS as DET_COUNTS
from jit_tests.fuzz import generate_engine, DEFAULT_COUNTS as FUZZ_COUNTS


# Each test runs a small slice of the matrix (default 50 cases per
# category per pytest worker). Tune via env vars:
#   JIT_SUITE_SLICE=200  -> 200 cases per category per pytest run
#   JIT_SUITE_OPT=cold   -> force cold for everything (fastest)
SLICE = int(os.environ.get("JIT_SUITE_SLICE", "50"))
OPT_STATE = os.environ.get("JIT_SUITE_OPT", "")


def _runner() -> Runner:
    return Runner(reference=StateController(), candidate=StateController())


def _force_opt(case):
    if not OPT_STATE:
        return case
    return case.with_opt_state(OPT_STATE)


@pytest.fixture(scope="module")
def runner() -> Runner:
    return _runner()


# ---------------------------------------------------------------------------
# Deterministic suites
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("category", list(DET_COUNTS))
def test_deterministic_category(runner: Runner, category: str) -> None:
    failures = []
    for i, case in enumerate(generate_category(category, n=SLICE)):
        if i >= SLICE:
            break
        case = _force_opt(case)
        r = runner.run_one(case)
        if not r.passed:
            failures.append((case.id, r.reason[:200]))
    assert not failures, f"{len(failures)} failures in {category}:\n" + "\n".join(
        f"- {cid}: {msg}" for cid, msg in failures[:5]
    )


# ---------------------------------------------------------------------------
# Fuzz engines (deterministic seed; small slice for fast pytest runs)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("engine", list(FUZZ_COUNTS))
def test_fuzz_engine(runner: Runner, engine: str) -> None:
    failures = []
    for i, case in enumerate(generate_engine(engine, n=SLICE)):
        if i >= SLICE:
            break
        case = _force_opt(case)
        r = runner.run_one(case)
        if not r.passed:
            failures.append((case.id, r.reason[:200]))
    assert not failures, f"{len(failures)} failures in fuzz/{engine}:\n" + "\n".join(
        f"- {cid}: {msg}" for cid, msg in failures[:5]
    )
