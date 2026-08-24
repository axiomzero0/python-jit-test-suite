"""Deterministic test generators for the 200K workload matrix.

Each category exposes a generator function that yields :class:`TestCase`
objects. The generators are deterministic given a fixed seed (so the same
suite can be re-run reproducibly) and parameterized so the total count is
configurable (defaults match the design doc's 200K breakdown).

Total by default:

    language_semantics       30,000
    interpreter_tiers        15,000
    numeric                  25,000
    objects                  20,000
    containers               25,000
    strings                  15,000
    functions               20,000
    exceptions              10,000
    metaprogramming         10,000
    memory_gc               10,000
    ml_kernels             10,000
    real_world             10,000
    concurrency             5,000
    ---------------------------------
    Total                 200,000

Each generator lives in its own module and is re-exported here.
"""

from __future__ import annotations

from typing import Iterator

from ..harness import TestCase

from .language import generate as gen_language
from .interpreter_tiers import generate as gen_tiers
from .numeric import generate as gen_numeric
from .objects import generate as gen_objects
from .containers import generate as gen_containers
from .strings import generate as gen_strings
from .functions import generate as gen_functions
from .exceptions import generate as gen_exceptions
from .metaprogramming import generate as gen_meta
from .memory_gc import generate as gen_memgc
from .ml_kernels import generate as gen_ml
from .real_world import generate as gen_realworld
from .concurrency import generate as gen_concurrency


DEFAULT_COUNTS = {
    "language_semantics": 30_000,
    "interpreter_tiers": 15_000,
    "numeric": 25_000,
    "objects": 20_000,
    "containers": 25_000,
    "strings": 15_000,
    "functions": 20_000,
    "exceptions": 10_000,
    "metaprogramming": 10_000,
    "memory_gc": 10_000,
    "ml_kernels": 10_000,
    "real_world": 10_000,
    "concurrency": 5_000,
}


_GENERATORS = {
    "language_semantics": gen_language,
    "interpreter_tiers": gen_tiers,
    "numeric": gen_numeric,
    "objects": gen_objects,
    "containers": gen_containers,
    "strings": gen_strings,
    "functions": gen_functions,
    "exceptions": gen_exceptions,
    "metaprogramming": gen_meta,
    "memory_gc": gen_memgc,
    "ml_kernels": gen_ml,
    "real_world": gen_realworld,
    "concurrency": gen_concurrency,
}


def generate_all(
    *,
    counts: dict[str, int] | None = None,
    seed: int = 0xC0FFEE,
) -> Iterator[TestCase]:
    """Yield every deterministic test case across all categories."""
    counts = counts or DEFAULT_COUNTS
    for name, gen in _GENERATORS.items():
        n = counts.get(name, 0)
        if n <= 0:
            continue
        yield from gen(n=n, seed=seed + hash(name) % 10_000_000)


def generate_category(name: str, *, n: int | None = None, seed: int = 0) -> Iterator[TestCase]:
    if name not in _GENERATORS:
        raise KeyError(f"unknown category: {name!r}; known: {list(_GENERATORS)}")
    count = n if n is not None else DEFAULT_COUNTS[name]
    yield from _GENERATORS[name](n=count, seed=seed)


__all__ = ["DEFAULT_COUNTS", "generate_all", "generate_category"]
