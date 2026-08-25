"""Harness-level unit tests: normalize, oracle, runner, minimizer."""
from __future__ import annotations

import math

from jit_tests.harness import (
    Observation,
    StateController,
    TestCase,
    Runner,
    TagSet,
    normalize,
    values_equal,
    compare,
    run_cpython,
)


def test_normalize_nan_equal_to_nan():
    assert normalize(float("nan")) == normalize(float("nan"))


def test_normalize_neg_zero_equal_to_pos_zero():
    assert normalize(-0.0) == normalize(0.0)


def test_normalize_dict_order_independent():
    assert normalize({"a": 1, "b": 2}) == normalize({"b": 2, "a": 1})


def test_normalize_set_order_independent():
    assert normalize({1, 2, 3}) == normalize({3, 2, 1})


def test_normalize_exception():
    a = normalize(ValueError("foo"))
    b = normalize(ValueError("foo"))
    c = normalize(KeyError("foo"))
    assert a == b
    assert a != c


def test_values_equal_nested():
    a = {"x": [1, 2, {"y": {3, 4}}], "z": float("inf")}
    b = {"z": float("inf"), "x": [1, 2, {"y": {4, 3}}]}
    assert values_equal(a, b)


def test_run_cpython_captures_stdout():
    obs = run_cpython("print('hello')\nx = 42\n")
    assert obs.stdout == "hello\n"
    assert obs.exception is None


def test_run_cpython_captures_exception():
    src = "raise ValueError('boom')\n"
    obs = run_cpython(src)
    assert obs.exception is not None
    assert isinstance(obs.exception, ValueError)
    assert "boom" in str(obs.exception)


def test_compare_equal_observations():
    a = Observation(return_value=42)
    b = Observation(return_value=42)
    ok, _ = compare(a, b)
    assert ok


def test_compare_unequal_return():
    a = Observation(return_value=42)
    b = Observation(return_value=43)
    ok, _ = compare(a, b)
    assert not ok


def test_compare_exception_vs_return():
    a = Observation(exception=ValueError("x"))
    b = Observation(return_value=0)
    ok, _ = compare(a, b)
    assert not ok


def test_runner_cpython_vs_cpython_passes():
    runner = Runner(reference=StateController(), candidate=StateController())
    case = TestCase(
        source="def main():\n    return 1 + 2\n",
        tags=TagSet.make("language_semantics"),
        id="t1",
        category="language_semantics",
    )
    r = runner.run_one(case)
    assert r.passed, r.reason


def test_runner_catches_mismatched_jit():
    """If the candidate controller returns wrong results, the runner flags it.

    We simulate a buggy JIT by overriding StateController.run to return
    a fixed wrong observation."""
    class BuggyController(StateController):
        def run(self, source, *, inputs=None, opt_state="cold", capture_globals=(), timeout=None):
            return Observation(return_value=99999)

    runner = Runner(reference=StateController(), candidate=BuggyController())
    case = TestCase(
        source="def main():\n    return 1 + 2\n",
        tags=TagSet.make("language_semantics"),
        id="t2",
        category="language_semantics",
    )
    r = runner.run_one(case)
    assert not r.passed
    assert "return value differs" in r.reason
