"""Exceptions / control flow: 10K tests.

Axes:

    feature        : try_except | nested_try | try_else | try_finally |
                     except_in_loop | exc_in_function | exc_in_generator |
                     exc_during_deopt | finally_during_deopt |
                     re_raise | exception_chain | bare_except |
                     except_tuple | custom_exception
    opt_state      : all 6
"""

from __future__ import annotations

from typing import Iterator

from ..harness import OptState, TagSet, TestCase
from ._common import GridBuilder, param_grid


FEATURES = (
    "try_except", "nested_try", "try_else", "try_finally",
    "except_in_loop", "exc_in_function", "exc_in_generator",
    "exc_during_deopt", "finally_during_deopt",
    "re_raise", "exception_chain", "bare_except",
    "except_tuple", "custom_exception",
)
OPT_STATES = [OptState.COLD, OptState.WARM, OptState.HOT, OptState.VERY_HOT, OptState.DEOPT, OptState.REHEATED]


_TEMPLATES = {
    "try_except": (
        "try:\n    raise ValueError('x')\nexcept ValueError as e:\n    assert str(e) == 'x'\n"
    ),
    "nested_try": (
        "try:\n    try:\n        raise ValueError('inner')\n    except KeyError:\n        pass\nexcept ValueError as e:\n    assert str(e) == 'inner'\n"
    ),
    "try_else": (
        "result = None\n"
        "try:\n    x = 1\nexcept Exception:\n    result = 'caught'\nelse:\n    result = 'no_exc'\n"
        "assert result == 'no_exc'\n"
    ),
    "try_finally": (
        "ran_finally = False\n"
        "try:\n    raise ValueError('x')\nfinally:\n    ran_finally = True\n"
        "assert False, 'should have raised'\n"
        if False else
        "ran_finally = False\n"
        "try:\n    pass\nfinally:\n    ran_finally = True\n"
        "assert ran_finally is True\n"
    ),
    "except_in_loop": (
        "caught = 0\n"
        "for i in range(10):\n"
        "    try:\n        if i % 2 == 0:\n            raise ValueError(i)\n"
        "    except ValueError:\n        caught += 1\n"
        "assert caught == 5\n"
    ),
    "exc_in_function": (
        "def f(x):\n    if x < 0:\n        raise ValueError('negative')\n    return x * 2\n"
        "try:\n    f(-1)\nexcept ValueError:\n    pass\n"
        "assert f(5) == 10\n"
    ),
    "exc_in_generator": (
        "def gen():\n    yield 1\n    raise ValueError('gen')\n    yield 2\n"
        "g = gen()\nassert next(g) == 1\n"
        "try:\n    next(g)\nexcept ValueError:\n    pass\n"
    ),
    "exc_during_deopt": (
        "def f(x):\n    s = 0\n    for i in range(100):\n        if i == 50:\n            raise ValueError('mid')\n        s += i * x\n    return s\n"
        "try:\n    f(2)\nexcept ValueError:\n    pass\n"
    ),
    "finally_during_deopt": (
        "ran_finally = False\n"
        "def f():\n    try:\n        for i in range(100):\n            if i == 50:\n                raise RuntimeError()\n    finally:\n        global ran_finally\n        ran_finally = True\n"
        "try:\n    f()\nexcept RuntimeError:\n    pass\nassert ran_finally is True\n"
    ),
    "re_raise": (
        "def f():\n    try:\n        raise ValueError('x')\n    except ValueError:\n        raise\n"
        "try:\n    f()\nexcept ValueError as e:\n    assert str(e) == 'x'\n"
    ),
    "exception_chain": (
        "try:\n    try:\n        raise ValueError('first')\n    except ValueError:\n        raise KeyError('second') from None\nexcept KeyError as e:\n    assert str(e) == 'second'\n"
    ),
    "bare_except": (
        "try:\n    raise RuntimeError('x')\nexcept:\n    pass\n"
    ),
    "except_tuple": (
        "try:\n    raise KeyError('k')\nexcept (ValueError, KeyError):\n    pass\n"
    ),
    "custom_exception": (
        "class MyErr(Exception):\n    def __init__(self, code):\n        super().__init__(code)\n        self.code = code\n"
        "try:\n    raise MyErr(42)\nexcept MyErr as e:\n    assert e.code == 42\n"
    ),
}


def generate(*, n: int = 10_000, seed: int = 0) -> Iterator[TestCase]:
    gb = GridBuilder(category="exceptions", id_prefix="exc")
    grid = param_grid(feature=FEATURES, opt=OPT_STATES)

    materialized = list(gb.expand_simple(
        grid,
        lambda p: _TEMPLATES[p["feature"]],
        tags_fn=lambda p: TagSet.make(
            "exceptions",
            type_stability="monomorphic",
            control_flow=("loop" if "loop" in p["feature"] else "if_else"),
            call_behavior=("generator" if "generator" in p["feature"] else "direct"),
            opt_state=p["opt"].value,
            tags={"exception", p["feature"], "deoptimization"},
        ),
    ))

    for i in range(n):
        case = materialized[i % len(materialized)]
        yield TestCase(
            source=case.source,
            inputs=case.inputs,
            tags=case.tags,
            id=f"exc-{i:07d}",
            category=case.category,
        )
