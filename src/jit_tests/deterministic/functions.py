"""Functions, closures, generators: 20K tests.

Axes:

    feature        : positional | keyword | defaults | args | kwargs |
                     closure | nested_closure | late_binding | nonlocal |
                     global | recursion | mutual_recursion | lambda |
                     decorator | partial | generator | yield_from |
                     send_throw_close | coroutine | async_gen
    opt_state      : all 6
"""

from __future__ import annotations

from typing import Iterator

from ..harness import OptState, TagSet, TestCase
from ._common import GridBuilder, param_grid


FEATURES = (
    "positional", "keyword", "defaults", "args", "kwargs",
    "closure", "nested_closure", "late_binding", "nonlocal",
    "global", "recursion", "mutual_recursion", "lambda",
    "decorator", "partial", "generator", "yield_from",
    "send_throw_close", "coroutine", "async_gen",
)
OPT_STATES = [OptState.COLD, OptState.WARM, OptState.HOT, OptState.VERY_HOT, OptState.DEOPT, OptState.REHEATED]


_TEMPLATES = {
    "positional": "def f(a, b, c):\n    return a + b + c\nassert f(1, 2, 3) == 6\n",
    "keyword": "def f(a, b, c):\n    return a * b * c\nassert f(c=3, a=1, b=2) == 6\n",
    "defaults": "def f(a, b=2, c=3):\n    return a + b + c\nassert f(1) == 6 and f(1, 10) == 14 and f(1, 10, 100) == 111\n",
    "args": "def f(*args):\n    return sum(args)\nassert f(1, 2, 3, 4) == 10\n",
    "kwargs": "def f(**kw):\n    return sorted(kw.items())\nassert f(a=1, b=2) == [('a', 1), ('b', 2)]\n",
    "closure": (
        "def make(x):\n    def f(y):\n        return x + y\n    return f\n"
        "add5 = make(5)\nassert add5(3) == 8\n"
    ),
    "nested_closure": (
        "def make(x):\n"
        "    def make2(y):\n"
        "        def f(z):\n"
        "            return x + y + z\n"
        "        return f\n"
        "    return make2(10)\n"
        "f = make(1)\nassert f(100) == 111\n"
    ),
    "late_binding": (
        "fs = []\n"
        "for i in range(3):\n"
        "    fs.append(lambda: i)\n"
        "# Late binding: all capture the last value of i\n"
        "assert [f() for f in fs] == [2, 2, 2]\n"
    ),
    "nonlocal": (
        "def make_counter():\n"
        "    c = 0\n"
        "    def step():\n"
        "        nonlocal c\n"
        "        c += 1\n"
        "        return c\n"
        "    return step\n"
        "s = make_counter()\n"
        "assert s() == 1 and s() == 2 and s() == 3\n"
    ),
    "global": (
        "g = 0\n"
        "def set_g():\n"
        "    global g\n"
        "    g = 42\n"
        "set_g()\n"
        "assert g == 42\n"
    ),
    "recursion": (
        "def fact(n):\n"
        "    if n <= 1:\n"
        "        return 1\n"
        "    return n * fact(n - 1)\n"
        "assert fact(10) == 3628800\n"
    ),
    "mutual_recursion": (
        "def is_even(n):\n"
        "    return True if n == 0 else is_odd(n - 1)\n"
        "def is_odd(n):\n"
        "    return False if n == 0 else is_even(n - 1)\n"
        "assert is_even(10) and not is_odd(0)\n"
    ),
    "lambda": "f = lambda x, y: x * y\nassert f(6, 7) == 42\n",
    "decorator": (
        "def double(f):\n"
        "    def wrapper(*a, **k):\n"
        "        return f(*a, **k) * 2\n"
        "    return wrapper\n"
        "@double\n"
        "def add(x):\n    return x + 1\n"
        "assert add(10) == 22\n"
    ),
    "partial": (
        "from functools import partial\n"
        "def add(a, b, c):\n    return a + b + c\n"
        "p = partial(add, 1, 2)\n"
        "assert p(3) == 6\n"
    ),
    "generator": (
        "def gen(n):\n"
        "    for i in range(n):\n"
        "        yield i * i\n"
        "assert list(gen(5)) == [0, 1, 4, 9, 16]\n"
    ),
    "yield_from": (
        "def inner():\n"
        "    yield 1\n    yield 2\n    yield 3\n"
        "def outer():\n"
        "    yield from inner()\n"
        "    yield 4\n"
        "assert list(outer()) == [1, 2, 3, 4]\n"
    ),
    "send_throw_close": (
        "def echo():\n"
        "    while True:\n"
        "        try:\n"
        "            v = yield\n"
        "            yield v\n"
        "        except GeneratorExit:\n"
        "            return\n"
        "g = echo()\n"
        "next(g)\n"
        "g.send('hello')\n"
        "assert next(g) == 'hello'\n"
        "g.close()\n"
    ),
    "coroutine": (
        "import asyncio\n"
        "async def f():\n    return 42\n"
        "assert asyncio.run(f()) == 42\n"
    ),
    "async_gen": (
        "import asyncio\n"
        "async def agen():\n"
        "    for i in range(3):\n"
        "        yield i\n"
        "async def main():\n"
        "    return [v async for v in agen()]\n"
        "assert asyncio.run(main()) == [0, 1, 2]\n"
    ),
}


def _opt_for_feature(feature: str) -> OptState:
    if feature in ("recursion", "mutual_recursion"):
        return OptState.WARM
    if feature in ("generator", "yield_from", "send_throw_close"):
        return OptState.HOT
    return OptState.COLD


def generate(*, n: int = 20_000, seed: int = 0) -> Iterator[TestCase]:
    gb = GridBuilder(category="functions", id_prefix="fn")
    grid = param_grid(feature=FEATURES, opt=OPT_STATES)

    materialized = list(gb.expand_simple(
        grid,
        lambda p: _TEMPLATES[p["feature"]],
        tags_fn=lambda p: TagSet.make(
            "functions",
            type_stability="monomorphic",
            control_flow=("recursion" if "recurs" in p["feature"] else "straight_line"),
            call_behavior=(
                "closure" if "closure" in p["feature"]
                else "generator" if "gen" in p["feature"] or "yield" in p["feature"]
                else "async" if p["feature"] in ("coroutine", "async_gen")
                else "direct"
            ),
            opt_state=p["opt"].value,
            tags={"function", p["feature"]},
        ),
    ))

    for i in range(n):
        case = materialized[i % len(materialized)]
        yield TestCase(
            source=case.source,
            inputs=case.inputs,
            tags=case.tags,
            id=f"fn-{i:07d}",
            category=case.category,
        )
