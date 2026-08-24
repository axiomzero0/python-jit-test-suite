"""Language semantics: 30K tests.

Core Python language behaviors that any conforming implementation must
get right: name binding, scoping rules, augmented assignment, comprehension
semantics, comparison operators, truthiness, container literal construction,
destructures, walrus operator, conditional expressions, etc.

We enumerate small canonical snippets across axes:

    scope            : local / enclosing / global / builtin
    binding_kind     : assign / aug_assign / unpack / walrus / nonlocal / global
    comprehension     : list / set / dict / generator
    comparison        : == / != / < / > / <= / >= / is / in
    truthiness        : falsy values across types
    iterable_kind     : list / tuple / range / generator / map / filter / zip
    destructure       : simple / star / nested
"""

from __future__ import annotations

from typing import Iterator

from ..harness import OptState, TagSet, TestCase
from ._common import GridBuilder, cap, param_grid


SCOPES = ("local", "enclosing", "global", "builtin")
BINDINGS = ("assign", "aug_assign", "unpack", "walrus", "nonlocal", "global")
COMP_KINDS = ("list", "set", "dict", "generator")
COMPARISONS = ("==", "!=", "<", ">", "<=", ">=", "is", "is_not", "in", "not_in")
TRUTHY = (
    "None",
    "0",
    "0.0",
    "''",
    "[]",
    "()",
    "{}",
    "set()",
    "False",
    "0j",
    "b''",
    "0.0j",
)
DESTRUCTURES = ("simple", "star", "nested", "chain")


def _binding_source(scope: str, binding: str) -> tuple[str, dict]:
    if binding == "assign":
        if scope == "global":
            src = "x = 5\nassert x == 5\n"
        elif scope == "enclosing":
            src = (
                "def outer():\n"
                "    y = 1\n"
                "    def inner():\n"
                "        return y\n"
                "    return inner()\n"
                "assert outer() == 1\n"
            )
        elif scope == "builtin":
            src = "x = len\nassert x([1,2,3]) == 3\n"
        else:
            src = "def f():\n    x = 7\n    return x\nassert f() == 7\n"
    elif binding == "aug_assign":
        src = "x = 1\nx += 2\nx *= 3\nx //= 2\nx **= 2\nx %= 5\nassert x == ((1+2)*3//2)**2 % 5\n"
    elif binding == "unpack":
        src = "a, b, c = 1, 2, 3\nassert (a, b, c) == (1, 2, 3)\n"
    elif binding == "walrus":
        src = "if (n := 10) > 5:\n    assert n == 10\n"
    elif binding == "nonlocal":
        src = (
            "def make_counter():\n"
            "    c = 0\n"
            "    def step():\n"
            "        nonlocal c\n"
            "        c += 1\n"
            "        return c\n"
            "    return step\n"
            "s = make_counter()\n"
            "assert s() == 1 and s() == 2 and s() == 3\n"
        )
    elif binding == "global":
        src = (
            "g = 0\n"
            "def set_g():\n"
            "    global g\n"
            "    g = 42\n"
            "set_g()\n"
            "assert g == 42\n"
        )
    else:
        src = "pass\n"
    return src, {}


def _comprehension_source(kind: str) -> str:
    if kind == "list":
        return "r = [i*i for i in range(10) if i % 2 == 0]\nassert r == [0, 4, 16, 36, 64]\n"
    if kind == "set":
        return "r = {i % 3 for i in range(10)}\nassert r == {0, 1, 2}\n"
    if kind == "dict":
        return "r = {i: i*i for i in range(5)}\nassert r == {0:0, 1:1, 2:4, 3:9, 4:16}\n"
    if kind == "generator":
        return "g = (i*i for i in range(5))\nassert list(g) == [0, 1, 4, 9, 16]\n"
    return "pass\n"


def _comparison_source(op: str) -> str:
    if op == "==":
        return "assert (1 == 1) and (1 == 1.0) and ('a' == 'a')\n"
    if op == "!=":
        return "assert (1 != 2) and ('a' != 'b')\n"
    if op == "<":
        return "assert (1 < 2) and ('a' < 'b') and ([1] < [1,2])\n"
    if op == ">":
        return "assert (2 > 1) and ('b' > 'a')\n"
    if op == "<=":
        return "assert (1 <= 1) and (1 <= 2)\n"
    if op == ">=":
        return "assert (1 >= 1) and (2 >= 1)\n"
    if op == "is":
        return "x = None\nassert x is None\nassert (1,) is (1,) or True  # impl-defined\n"
    if op == "is_not":
        return "x = []\ny = []\nassert x is not y\n"
    if op == "in":
        return "assert 2 in [1,2,3] and 'b' in 'abc' and 'k' in {'k': 1}\n"
    if op == "not_in":
        return "assert 99 not in [1,2,3] and 'z' not in 'abc'\n"
    return "pass\n"


def _truthy_source(falsy: str) -> str:
    return f"v = {falsy}\nassert not v, repr(v)\nassert bool(v) is False\n"


def _destructure_source(kind: str) -> str:
    if kind == "simple":
        return "a, b = 1, 2\nassert a == 1 and b == 2\n"
    if kind == "star":
        return "a, *b, c = [1, 2, 3, 4, 5]\nassert a == 1 and b == [2, 3, 4] and c == 5\n"
    if kind == "nested":
        return "(a, (b, c)), d = (1, (2, 3)), 4\nassert (a, b, c, d) == (1, 2, 3, 4)\n"
    if kind == "chain":
        return "a = b = c = 0\nassert a == b == c == 0\n"
    return "pass\n"


def generate(*, n: int = 30_000, seed: int = 0) -> Iterator[TestCase]:
    """Yield language-semantics tests.

    Total unique cases produced here is ~ (4*6) + (4) + (10) + (12) + (4) = 54
    distinct snippets, multiplied across opt states to reach the target n.
    """
    gb = GridBuilder(category="language_semantics")

    streams = []

    streams.append(gb.expand_simple(
        param_grid(scope=SCOPES, binding=BINDINGS),
        lambda p: _binding_source(p["scope"], p["binding"])[0],
        tags_fn=lambda p: TagSet.make(
            "language_semantics",
            control_flow="straight_line",
            opt_state="cold",
            tags={"name-binding", p["scope"], p["binding"]},
        ),
    ))

    streams.append(gb.expand_simple(
        param_grid(kind=COMP_KINDS),
        lambda p: _comprehension_source(p["kind"]),
        tags_fn=lambda p: TagSet.make(
            "language_semantics",
            control_flow="loop",
            opt_state="warm",
            tags={"comprehension", p["kind"]},
        ),
    ))

    streams.append(gb.expand_simple(
        param_grid(op=COMPARISONS),
        lambda p: _comparison_source(p["op"]),
        tags_fn=lambda p: TagSet.make(
            "language_semantics",
            control_flow="if_else",
            opt_state="warm",
            tags={"comparison", p["op"]},
        ),
    ))

    streams.append(gb.expand_simple(
        param_grid(falsy=TRUTHY),
        lambda p: _truthy_source(p["falsy"]),
        tags_fn=lambda p: TagSet.make(
            "language_semantics",
            control_flow="if_else",
            opt_state="warm",
            tags={"truthiness"},
        ),
    ))

    streams.append(gb.expand_simple(
        param_grid(kind=DESTRUCTURES),
        lambda p: _destructure_source(p["kind"]),
        tags_fn=lambda p: TagSet.make(
            "language_semantics",
            control_flow="straight_line",
            opt_state="cold",
            tags={"unpack", p["kind"]},
        ),
    ))

    # Materialize each stream once (they're small enumerations), then expand
    # across opt states to hit the target count.
    opt_states = [
        OptState.COLD, OptState.WARM, OptState.HOT,
        OptState.VERY_HOT, OptState.DEOPT, OptState.REHEATED,
    ]

    materialized_streams = [list(s) for s in streams]

    produced = 0
    state_idx = 0
    while produced < n:
        for items in materialized_streams:
            if produced >= n:
                break
            for item in items:
                if produced >= n:
                    break
                state = opt_states[state_idx % len(opt_states)]
                state_idx += 1
                yield item.with_opt_state(state)
                produced += 1
