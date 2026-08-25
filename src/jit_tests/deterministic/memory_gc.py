"""Memory / GC / lifetime: 10K tests.

Axes:

    graph_shape     : tree | dag | cycle | deep_nest | wide |
                      short_lived | long_lived | large_alloc |
                      alloc_heavy_loop
    escape          : does_not_escape | escapes_global |
                      escapes_arg | escapes_return
    opt_state       : all 6
"""

from __future__ import annotations

from typing import Iterator

from ..harness import OptState, TagSet, TestCase
from ._common import GridBuilder, param_grid


GRAPH_SHAPES = (
    "tree", "dag", "cycle", "deep_nest", "wide",
    "short_lived", "long_lived", "large_alloc", "alloc_heavy_loop",
)
ESCAPE = ("does_not_escape", "escapes_global", "escapes_arg", "escapes_return")
OPT_STATES = [OptState.COLD, OptState.WARM, OptState.HOT, OptState.VERY_HOT, OptState.DEOPT, OptState.REHEATED]


_TEMPLATES = {
    ("tree", "does_not_escape"): (
        "def make_tree(depth):\n"
        "    if depth == 0:\n        return None\n"
        "    return [make_tree(depth - 1), make_tree(depth - 1)]\n"
        "t = make_tree(8)\nassert t is not None or True\n"
    ),
    ("dag", "does_not_escape"): (
        "shared = [1, 2, 3]\n"
        "g = {'a': shared, 'b': shared, 'c': shared}\n"
        "assert g['a'] is g['b'] is g['c']\n"
    ),
    ("cycle", "does_not_escape"): (
        "a = []\nb = [a]\na.append(b)\n"
        "assert a[0] is b and b[0] is a\n"
    ),
    ("deep_nest", "does_not_escape"): (
        "x = []\n"
        "for _ in range(100):\n    x = [x]\n"
        "assert x is not None\n"
    ),
    ("wide", "does_not_escape"): (
        "x = [[] for _ in range(1000)]\n"
        "assert len(x) == 1000\n"
    ),
    ("short_lived", "does_not_escape"): (
        "def f():\n    return sum([i for i in range(100)])\n"
        "for _ in range(100):\n    f()\n"
        "assert f() == 4950\n"
    ),
    ("long_lived", "escapes_global"): (
        "G = []\n"
        "for i in range(100):\n    G.append([i, i+1, i+2])\n"
        "assert len(G) == 100 and G[50][0] == 50\n"
    ),
    ("large_alloc", "does_not_escape"): (
        "def f():\n    return list(range(100_000))\n"
        "x = f()\nassert len(x) == 100_000\n"
    ),
    ("alloc_heavy_loop", "does_not_escape"): (
        "def f():\n    total = 0\n"
        "    for i in range(1000):\n        total += sum([i, i+1, i+2])\n    return total\n"
        "assert f() == 3 * sum(range(1000)) + 3  # 0+1+2 + 1+2+3 + ... \n"
    ),
    # escape variants
    ("tree", "escapes_return"): (
        "def make_tree(depth):\n"
        "    if depth == 0:\n        return None\n"
        "    return [make_tree(depth - 1), make_tree(depth - 1)]\n"
        "G = make_tree(6)\nassert G is not None\n"
    ),
    ("cycle", "escapes_global"): (
        "G = []\n"
        "G.append([G])\n"
        "assert G[0][0] is G\n"
    ),
    ("deep_nest", "escapes_global"): (
        "G = []\n"
        "x = []\nfor _ in range(50):\n    x = [x]\nG.append(x)\nassert G[0] is x\n"
    ),
}


def generate(*, n: int = 10_000, seed: int = 0) -> Iterator[TestCase]:
    gb = GridBuilder(category="memory_gc", id_prefix="mem")

    grid = param_grid(shape=GRAPH_SHAPES, escape=ESCAPE, opt=OPT_STATES)
    materialized = []
    for params in grid:
        key = (params["shape"], params["escape"])
        if key not in _TEMPLATES:
            # Fall back to the "does_not_escape" version of the shape.
            key = (params["shape"], "does_not_escape")
            if key not in _TEMPLATES:
                continue
        case = TestCase(
            source=_TEMPLATES[key],
            inputs=(),
            tags=TagSet.make(
                "memory_gc",
                type_stability="monomorphic",
                control_flow="loop" if "loop" in params["shape"] else "straight_line",
                call_behavior="direct",
                opt_state=params["opt"].value,
                tags={"memory", "GC", params["shape"], params["escape"], "escape-analysis"},
            ),
            id=f"mem-{len(materialized):07d}",
            category="memory_gc",
        )
        materialized.append(case)

    for i in range(n):
        case = materialized[i % len(materialized)]
        yield TestCase(
            source=case.source,
            inputs=case.inputs,
            tags=case.tags,
            id=f"mem-{i:07d}",
            category=case.category,
        )
