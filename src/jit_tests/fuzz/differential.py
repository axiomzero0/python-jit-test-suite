"""Differential fuzzer: run programs under multiple implementations and
compare observable behavior.

For each program, we tag it as a differential test case. The Runner
executes it under reference (CPython) and candidate (JIT) and compares.

Default: 200K differential executions. Each yields one TestCase that the
Runner handles by running both implementations and comparing.

The differential engine combines small programs (drawn from the same
seed library used by the mutation fuzzer, plus a few extras with more
extreme behavior) with random opt states.
"""

from __future__ import annotations

import random
from typing import Iterator

from ..harness import OptState, TagSet, TestCase


_PROGRAMS = [
    # Numeric edge cases
    "def main():\n    return 2 ** 64 + 1\n",
    "def main():\n    return 0.1 + 0.2\n",
    "def main():\n    x = float('inf')\n    return x - x\n",
    "def main():\n    x = float('nan')\n    return x != x\n",
    "def main():\n    return (-1) ** 0.5\n",
    # Container semantics
    "def main():\n    a = [1, 2, 3]\n    b = a\n    b.append(4)\n    return len(a)\n",
    "def main():\n    d = {i: i*i for i in range(10)}\n    return d.get(5, -1) + d.get(99, -1)\n",
    # Exception edge cases
    "def main():\n    try:\n        return {}['missing']\n    except KeyError as e:\n        return str(e)\n",
    "def main():\n    try:\n        return 1 / 0\n    except ZeroDivisionError:\n        return 'caught'\n",
    # Generator semantics
    "def main():\n    def g():\n        yield 1\n        yield 2\n        yield 3\n    return list(g())\n",
    "def main():\n    def g():\n        yield 1\n        raise RuntimeError('boom')\n    try:\n        return list(g())\n    except RuntimeError:\n        return 'caught'\n",
    # Closures
    "def main():\n    def make(x):\n        def f():\n            return x\n        return f\n    return make(42)()\n",
    # Class semantics
    "class A:\n    x = 1\n"
    "def main():\n    a = A()\n    v1 = a.x\n    A.x = 2\n    v2 = a.x\n    return (v1, v2)\n",
    # Boolean / short circuit
    "def main():\n    x = []\n    return x and 'truthy' or 'falsy'\n",
    "def main():\n    return True and 0 or 'x'\n",
    # Numeric reductions
    "def main():\n    s = 0\n    for i in range(100):\n        s += i\n    return s\n",
    "def main():\n    s = 0.0\n    for i in range(100):\n        s += i * 0.1\n    return s\n",
    # Mutation during iteration
    "def main():\n    x = [1, 2, 3]\n    seen = []\n    for v in x:\n        seen.append(v)\n        if len(x) < 5:\n            x.append(len(x) + 1)\n    return seen\n",
    # String formatting
    "def main():\n    return '{} + {} = {}'.format(1, 2, 3)\n",
    "def main():\n    return sum(ord(c) for c in 'hello world')\n",
    # Walrus
    "def main():\n    if (n := 10) > 5:\n        return n\n    return 0\n",
    # Conditional expression
    "def main():\n    return 'yes' if 1 > 0 else 'no'\n",
    # Nested data structures
    "def main():\n    a = [[0] * 3 for _ in range(3)]\n    a[0][0] = 99\n    return a[0][0] + a[1][0] + a[2][0]\n",
    # Tuple unpacking
    "def main():\n    a, b, *c = range(5)\n    return (a, b, c)\n",
    # F-string
    "def main():\n    x = 42\n    return f'{x=}'\n",
]


def generate(*, n: int = 200_000, seed: int = 0) -> Iterator[TestCase]:
    rng = random.Random(seed)
    for i in range(n):
        src = rng.choice(_PROGRAMS)
        opt = rng.choices(
            [OptState.COLD, OptState.WARM, OptState.HOT, OptState.VERY_HOT, OptState.DEOPT],
            weights=[3, 3, 2, 1, 1], k=1)[0]
        yield TestCase(
            source=src,
            inputs=(),
            tags=TagSet.make(
                "language_semantics",
                type_stability="unknown",
                control_flow="straight_line",
                call_behavior="direct",
                opt_state=opt.value,
                tags={"fuzz", "differential", "CPython-vs-JIT"},
            ),
            id=f"fuzz-diff-{i:08d}",
            category="fuzz_differential",
        )
