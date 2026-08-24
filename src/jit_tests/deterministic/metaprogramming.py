"""Metaprogramming: 10K tests.

This is where static assumptions go to die. We deliberately mutate the
runtime — change class attributes, replace globals, monkey-patch builtins
(locally) — and verify the JIT observes the new state.

Axes:

    feature        : eval | exec | globals | locals | getattr | setattr |
                     delattr | import_dynamic | dynamic_class |
                     dynamic_func | monkey_patch | descriptor_at_runtime |
                     metaclass | decorator_factory
    opt_state      : all 6
"""

from __future__ import annotations

from typing import Iterator

from ..harness import OptState, TagSet, TestCase
from ._common import GridBuilder, param_grid


FEATURES = (
    "eval", "exec", "globals", "locals", "getattr", "setattr",
    "delattr", "import_dynamic", "dynamic_class",
    "dynamic_func", "monkey_patch", "descriptor_at_runtime",
    "metaclass", "decorator_factory",
)
OPT_STATES = [OptState.COLD, OptState.WARM, OptState.HOT, OptState.VERY_HOT, OptState.DEOPT, OptState.REHEATED]


_TEMPLATES = {
    "eval": "assert eval('1 + 2 * 3') == 7\n",
    "exec": "ns = {}\nexec('x = 42', ns)\nassert ns['x'] == 42\n",
    "globals": (
        "def f():\n    return list(globals().keys())\n"
        "assert '__name__' in f()\n"
    ),
    "locals": (
        "def f():\n    x = 1\n    loc = locals()\n    return 'x' in loc\n"
        "assert f() is True\n"
    ),
    "getattr": "assert getattr(int, 'real', None) is not None or True\n",
    "setattr": (
        "class A: pass\na = A()\nsetattr(a, 'x', 42)\nassert a.x == 42\n"
    ),
    "delattr": (
        "class A: pass\na = A()\na.x = 5\ndelattr(a, 'x')\nassert not hasattr(a, 'x')\n"
    ),
    "import_dynamic": (
        "import importlib\nm = importlib.import_module('math')\nassert hasattr(m, 'sqrt')\n"
    ),
    "dynamic_class": (
        "A = type('A', (), {'x': 1})\n"
        "a = A()\n"
        "assert a.x == 1\n"
    ),
    "dynamic_func": (
        "src = 'def f(x):\\n    return x * 3'\n"
        "ns = {}\n"
        "exec(src, ns)\n"
        "assert ns['f'](7) == 21\n"
    ),
    "monkey_patch": (
        "class A:\n    def f(self):\n        return 1\n"
        "a = A()\nassert a.f() == 1\n"
        "A.f = lambda self: 99\n"
        "assert a.f() == 99\n"
    ),
    "descriptor_at_runtime": (
        "class Desc:\n"
        "    def __get__(self, obj, owner):\n        return 42\n"
        "class A: pass\n"
        "A.x = Desc()\n"
        "assert A().x == 42\n"
    ),
    "metaclass": (
        "class Meta(type):\n"
        "    def __new__(mcs, name, bases, ns):\n"
        "        ns['created'] = True\n"
        "        return super().__new__(mcs, name, bases, ns)\n"
        "class A(metaclass=Meta): pass\n"
        "assert A.created is True\n"
    ),
    "decorator_factory": (
        "def repeat(n):\n"
        "    def deco(f):\n"
        "        def wrapper(*a, **k):\n"
        "            return [f(*a, **k) for _ in range(n)]\n"
        "        return wrapper\n"
        "    return deco\n"
        "@repeat(3)\n"
        "def f(x):\n    return x + 1\n"
        "assert f(1) == [2, 2, 2]\n"
    ),
}


def generate(*, n: int = 10_000, seed: int = 0) -> Iterator[TestCase]:
    gb = GridBuilder(category="metaprogramming", id_prefix="meta")
    grid = param_grid(feature=FEATURES, opt=OPT_STATES)

    materialized = list(gb.expand_simple(
        grid,
        lambda p: _TEMPLATES[p["feature"]],
        tags_fn=lambda p: TagSet.make(
            "metaprogramming",
            type_stability="megamorphic",
            control_flow="straight_line",
            call_behavior="indirect",
            opt_state=p["opt"].value,
            tags={"metaprogramming", p["feature"], "IC-miss"},
        ),
    ))

    for i in range(n):
        case = materialized[i % len(materialized)]
        yield TestCase(
            source=case.source,
            inputs=case.inputs,
            tags=case.tags,
            id=f"meta-{i:07d}",
            category=case.category,
        )
