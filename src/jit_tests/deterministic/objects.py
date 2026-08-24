"""Object model: 20K tests.

Python's object model is where optimizers most often lie to themselves.

Axes:

    feature        : class_creation | inheritance | multiple_inheritance |
                     super_call | staticmethod | classmethod | property |
                     descriptor | __getattribute__ | __getattr__ |
                     __setattr__ | __slots__ | dataclass | dynamic_attr |
                     instance_dict | ic_mutation | hierarchy_mutation
    opt_state     : all 6 states
"""

from __future__ import annotations

from typing import Iterator

from ..harness import OptState, TagSet, TestCase
from ._common import GridBuilder, param_grid


FEATURES = (
    "class_creation",
    "inheritance",
    "multiple_inheritance",
    "super_call",
    "staticmethod",
    "classmethod",
    "property",
    "descriptor",
    "getattribute",
    "getattr_fallback",
    "setattr_custom",
    "slots",
    "dataclass",
    "dynamic_attr",
    "instance_dict",
    "ic_mutation",
    "hierarchy_mutation",
)
OPT_STATES = [OptState.COLD, OptState.WARM, OptState.HOT, OptState.VERY_HOT, OptState.DEOPT, OptState.REHEATED]


_TEMPLATES = {
    "class_creation": (
        "class A:\n    def __init__(self, x):\n        self.x = x\n"
        "a = A(42)\nassert a.x == 42\n"
    ),
    "inheritance": (
        "class A:\n    def f(self):\n        return 1\n"
        "class B(A):\n    def g(self):\n        return 2\n"
        "b = B()\nassert b.f() == 1 and b.g() == 2\n"
    ),
    "multiple_inheritance": (
        "class A:\n    def f(self):\n        return 1\n"
        "class B:\n    def g(self):\n        return 2\n"
        "class C(A, B):\n    pass\n"
        "c = C()\nassert c.f() == 1 and c.g() == 2\n"
    ),
    "super_call": (
        "class A:\n    def __init__(self):\n        self.x = 1\n"
        "class B(A):\n    def __init__(self):\n        super().__init__()\n        self.x += 1\n"
        "b = B()\nassert b.x == 2\n"
    ),
    "staticmethod": (
        "class A:\n    @staticmethod\n    def f(x):\n        return x * 2\n"
        "assert A.f(21) == 42\n"
    ),
    "classmethod": (
        "class A:\n    @classmethod\n    def f(cls, x):\n        return cls.__name__, x\n"
        "assert A.f(7) == ('A', 7)\n"
    ),
    "property": (
        "class A:\n    def __init__(self):\n        self._x = 0\n"
        "    @property\n    def x(self):\n        return self._x\n"
        "    @x.setter\n    def x(self, v):\n        self._x = v + 1\n"
        "a = A()\na.x = 10\nassert a.x == 11\n"
    ),
    "descriptor": (
        "class Desc:\n"
        "    def __get__(self, obj, owner):\n        return 42\n"
        "class A:\n    v = Desc()\n"
        "assert A().v == 42\n"
    ),
    "getattribute": (
        "class A:\n"
        "    def __getattribute__(self, name):\n"
        "        return 'X' if name == 'x' else super().__getattribute__(name)\n"
        "a = A()\nassert a.x == 'X'\n"
    ),
    "getattr_fallback": (
        "class A:\n"
        "    def __getattr__(self, name):\n"
        "        if name == 'magic':\n            return 99\n"
        "        raise AttributeError(name)\n"
        "a = A()\nassert a.magic == 99\n"
    ),
    "setattr_custom": (
        "class A:\n"
        "    def __setattr__(self, name, value):\n"
        "        super().__setattr__(name, value * 2)\n"
        "a = A()\na.x = 21\nassert a.x == 42\n"
    ),
    "slots": (
        "class A:\n    __slots__ = ('x', 'y')\n"
        "a = A()\na.x = 1\na.y = 2\nassert a.x + a.y == 3\n"
    ),
    "dataclass": (
        "from dataclasses import dataclass\n"
        "@dataclass\nclass A:\n    x: int = 0\n    y: int = 0\n"
        "a = A(1, 2)\nassert a.x == 1 and a.y == 2\nassert a == A(1, 2)\n"
    ),
    "dynamic_attr": (
        "class A: pass\n"
        "a = A()\na.x = 1\na.y = 2\nassert a.x + a.y == 3\n"
        "del a.x\nassert not hasattr(a, 'x')\n"
    ),
    "instance_dict": (
        "class A: pass\n"
        "a = A()\nv = vars(a)\nv['z'] = 100\nassert a.z == 100\n"
    ),
    "ic_mutation": (
        # Initially monomorphic, then becomes polymorphic
        "class A:\n    x = 1\n"
        "class B:\n    x = 2\n"
        "class C:\n    x = 3\n"
        "def f(o):\n    return o.x\n"
        "a, b, c = A(), B(), C()\n"
        "assert f(a) == 1\n"
        "assert f(b) == 2\n"
        "assert f(c) == 3\n"
        "A.x = 100\nassert f(a) == 100\n"
    ),
    "hierarchy_mutation": (
        "class A:\n    x = 1\n"
        "class B(A):\n    pass\n"
        "b = B()\nassert b.x == 1\n"
        "class B(A):\n    x = 99\n"
        "b2 = B()\nassert b2.x == 99\n"
    ),
}


def generate(*, n: int = 20_000, seed: int = 0) -> Iterator[TestCase]:
    gb = GridBuilder(category="objects", id_prefix="obj")
    grid = param_grid(feature=FEATURES, opt=OPT_STATES)
    materialized = list(gb.expand_simple(
        grid,
        lambda p: _TEMPLATES[p["feature"]],
        tags_fn=lambda p: TagSet.make(
            "objects",
            type_stability=("polymorphic" if p["feature"] in ("ic_mutation", "hierarchy_mutation") else "monomorphic"),
            control_flow="if_else" if p["feature"] in ("getattr_fallback", "getattribute") else "straight_line",
            call_behavior="method",
            opt_state=p["opt"].value,
            tags={"object-model", p["feature"], "inline-cache"},
        ),
    ))

    for i in range(n):
        case = materialized[i % len(materialized)]
        yield TestCase(
            source=case.source,
            inputs=case.inputs,
            tags=case.tags,
            id=f"obj-{i:07d}",
            category=case.category,
        )
