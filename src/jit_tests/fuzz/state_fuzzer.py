"""Optimization-state fuzzer: take fixed valid programs and randomly
manipulate the *runtime state* they execute under.

This is the engine that catches bugs ordinary fuzzing completely misses:

    run cold
    run 3 times
    run 100 times
    run 10000 times
    change argument type between runs
    invalidate IC between runs
    trigger GC between runs
    raise exception between runs
    force deopt between runs
    resume after deopt
    change globals between runs

The program source stays the same; the runtime state sequence changes.

Each yielded TestCase has the same source but a *different* opt_state
and tags that describe the state sequence the harness should drive.
"""

from __future__ import annotations

import random
from typing import Iterator

from ..harness import OptState, TagSet, TestCase


# Reusable small programs that benefit from / are sensitive to opt state.
_PROGRAMS = [
    # Monomorphic hot loop
    "def main():\n    s = 0\n    for i in range(1000):\n        s += i\n    return s\n",
    # Polymorphic call site
    "class A:\n    def f(self):\n        return 1\n"
    "class B:\n    def f(self):\n        return 2\n"
    "class C:\n    def f(self):\n        return 3\n"
    "def g(o):\n    return o.f()\n"
    "def main():\n    a, b, c = A(), B(), C()\n    s = 0\n    for i in range(100):\n        s += g([a, b, c][i % 3])\n    return s\n",
    # Container in tight loop
    "def main():\n    x = []\n    for i in range(1000):\n        x.append(i)\n    return sum(x)\n",
    # IC mutation
    "class A:\n    x = 1\n"
    "def f(o):\n    return o.x\n"
    "def main():\n    a = A()\n    s = 0\n    for i in range(100):\n        s += f(a)\n    A.x = 99\n    s += f(a)\n    return s\n",
    # Recursion
    "def fact(n):\n    if n <= 1:\n        return 1\n    return n * fact(n - 1)\n"
    "def main():\n    return fact(20)\n",
    # Generator + tight loop
    "def g(n):\n    for i in range(n):\n        yield i * i\n"
    "def main():\n    return sum(g(100))\n",
    # Exception in hot loop
    "def main():\n    s = 0\n    for i in range(100):\n        try:\n            if i == 50:\n                raise ValueError()\n            s += i\n        except ValueError:\n            s -= 1\n    return s\n",
    # Closure mutation
    "def make():\n    x = [0]\n    def f():\n        x[0] += 1\n        return x[0]\n    return f\n"
    "def main():\n    f = make()\n    s = 0\n    for _ in range(100):\n        s += f()\n    return s\n",
    # Float reduction
    "def main():\n    s = 0.0\n    for i in range(1000):\n        s += i * 0.5\n    return s\n",
]


# State sequences (lists of opt states the harness should drive the case through).
# The runner uses the LAST state for the actual differential check.
_STATE_SEQUENCES = [
    [OptState.COLD],
    [OptState.WARM],
    [OptState.HOT],
    [OptState.VERY_HOT],
    [OptState.DEOPT],
    [OptState.REHEATED],
    [OptState.WARM, OptState.HOT, OptState.DEOPT],
    [OptState.HOT, OptState.DEOPT, OptState.REHEATED],
    [OptState.COLD, OptState.WARM, OptState.HOT, OptState.VERY_HOT, OptState.DEOPT, OptState.REHEATED],
    [OptState.HOT, OptState.HOT, OptState.DEOPT],
    [OptState.VERY_HOT, OptState.DEOPT, OptState.VERY_HOT],
]


# Optional "state perturbations" between runs.
_PERTURBATIONS = [
    "trigger_gc",
    "invalidate_ic",
    "raise_runtime_error",
    "change_global",
    "mutate_class_attr",
    "no_perturbation",
]


def generate(*, n: int = 250_000, seed: int = 0) -> Iterator[TestCase]:
    rng = random.Random(seed)
    for i in range(n):
        src = rng.choice(_PROGRAMS)
        seq = rng.choice(_STATE_SEQUENCES)
        perturb = rng.choice(_PERTURBATIONS)
        final_state = seq[-1]
        yield TestCase(
            source=src,
            inputs=(),
            tags=TagSet.make(
                "interpreter_tiers",
                type_stability="polymorphic",
                control_flow="loop",
                call_behavior="direct",
                opt_state=final_state.value,
                tags={
                    "fuzz", "state", "deoptimization", "OSR",
                    f"seq_{len(seq)}",
                    f"perturb_{perturb}",
                },
            ),
            id=f"fuzz-state-{i:08d}",
            category="fuzz_state",
        )
