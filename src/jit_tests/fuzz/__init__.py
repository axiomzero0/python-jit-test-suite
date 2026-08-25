"""Fuzzing engines: 4 independent fuzzers + minimizer + regression store.

Engines (default counts to reach 1M):

    ast_fuzzer        - 300K valid Python ASTs
    mutation_fuzzer   - 250K mutations of seed programs
    state_fuzzer      - 250K optimization-state manipulations
    differential      - 200K CPython-vs-JIT differential runs

Each engine yields :class:`jit_tests.harness.TestCase` objects that the
Runner then executes. Failures are minimized by :mod:`.minimizer` and
stored as permanent regression tests by :mod:`.regressions`.
"""

from __future__ import annotations

from typing import Iterator

from ..harness import TestCase

from .ast_fuzzer import generate as gen_ast
from .mutation_fuzzer import generate as gen_mutation
from .state_fuzzer import generate as gen_state
from .differential import generate as gen_differential


DEFAULT_COUNTS = {
    "ast": 300_000,
    "mutation": 250_000,
    "state": 250_000,
    "differential": 200_000,
}


_ENGINES = {
    "ast": gen_ast,
    "mutation": gen_mutation,
    "state": gen_state,
    "differential": gen_differential,
}


def generate_all(
    *,
    counts: dict[str, int] | None = None,
    seed: int = 0xF123,
) -> Iterator[TestCase]:
    counts = counts or DEFAULT_COUNTS
    for name, gen in _ENGINES.items():
        n = counts.get(name, 0)
        if n <= 0:
            continue
        yield from gen(n=n, seed=seed + hash(name) % 10_000_000)


def generate_engine(name: str, *, n: int | None = None, seed: int = 0) -> Iterator[TestCase]:
    if name not in _ENGINES:
        raise KeyError(f"unknown fuzz engine: {name!r}; known: {list(_ENGINES)}")
    count = n if n is not None else DEFAULT_COUNTS[name]
    yield from _ENGINES[name](n=count, seed=seed)


__all__ = ["DEFAULT_COUNTS", "generate_all", "generate_engine"]
