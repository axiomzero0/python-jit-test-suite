"""Containers: 25K tests.

Lists, dicts, sets, tuples, plus aliasing scenarios that break naive
optimizers.

Axes:

    container     : list | dict | set | tuple | frozenset
    operation     : append | pop | insert | remove | slice | extend |
                    reverse | sort | iterate | mutate_during_iter |
                    lookup | resize | hash_collision
    key_type      : int | str | mixed | custom_obj | missing
    aliasing      : none | shallow | nested | cyclic
    opt_state     : all 6
"""

from __future__ import annotations

from typing import Iterator

from ..harness import OptState, TagSet, TestCase
from ._common import GridBuilder, param_grid


CONTAINERS = ("list", "dict", "set", "tuple", "frozenset")
OPERATIONS = (
    "append", "pop", "insert", "remove", "slice", "extend",
    "reverse", "sort", "iterate", "mutate_during_iter",
    "lookup", "resize", "hash_collision",
)
ALIASING = ("none", "shallow", "nested", "cyclic")
OPT_STATES = [OptState.COLD, OptState.WARM, OptState.HOT, OptState.VERY_HOT, OptState.DEOPT, OptState.REHEATED]


_TEMPLATES = {
    ("list", "append"): (
        "x = []\nfor i in range(100):\n    x.append(i)\n"
        "assert len(x) == 100 and x[0] == 0 and x[-1] == 99\n"
    ),
    ("list", "pop"): (
        "x = list(range(10))\nassert x.pop() == 9\nassert x.pop(0) == 0\nassert len(x) == 8\n"
    ),
    ("list", "insert"): (
        "x = [1, 2, 3]\nx.insert(1, 99)\nassert x == [1, 99, 2, 3]\n"
    ),
    ("list", "remove"): (
        "x = [1, 2, 3, 2]\nx.remove(2)\nassert x == [1, 3, 2]\n"
    ),
    ("list", "slice"): (
        "x = list(range(10))\nassert x[2:5] == [2, 3, 4]\nassert x[::-1] == list(range(9, -1, -1))\nassert x[::2] == [0, 2, 4, 6, 8]\n"
    ),
    ("list", "extend"): (
        "x = [1, 2]\nx.extend([3, 4])\nx += [5]\nassert x == [1, 2, 3, 4, 5]\n"
    ),
    ("list", "reverse"): (
        "x = [1, 2, 3]\nx.reverse()\nassert x == [3, 2, 1]\nassert list(reversed([1,2,3])) == [3,2,1]\n"
    ),
    ("list", "sort"): (
        "x = [3, 1, 2]\nx.sort()\nassert x == [1, 2, 3]\nx.sort(reverse=True)\nassert x == [3, 2, 1]\n"
    ),
    ("list", "iterate"): (
        "x = list(range(100))\ns = 0\nfor v in x:\n    s += v\nassert s == 4950\n"
    ),
    ("list", "mutate_during_iter"): (
        # Mutate by appending during iteration; well-defined for list iteration
        "x = [1, 2, 3]\nseen = []\nfor v in x:\n    seen.append(v)\n    if len(x) < 6:\n        x.append(len(x) + 1)\nassert seen == [1, 2, 3, 4, 5, 6]\n"
    ),
    ("list", "lookup"): "x = list(range(100))\nassert 50 in x and 999 not in x\n",
    ("list", "resize"): "x = []\nfor i in range(1000):\n    x.append(i)\nassert len(x) == 1000\n",
    ("list", "hash_collision"): "x = [1, 1, 1]\nassert x.count(1) == 3\n",

    ("dict", "append"): "d = {}\nfor i in range(100):\n    d[i] = i * 2\nassert d[50] == 100\n",
    ("dict", "pop"): "d = {'a': 1, 'b': 2}\nassert d.pop('a') == 1\nassert d.pop('missing', 99) == 99\n",
    ("dict", "insert"): "d = {1: 'a'}\nd[2] = 'b'\nassert d == {1: 'a', 2: 'b'}\n",
    ("dict", "remove"): "d = {1: 'a', 2: 'b'}\ndel d[1]\nassert d == {2: 'b'}\n",
    ("dict", "slice"): "d = {i: i*i for i in range(10)}\nkeys = [k for k in d if k < 5]\nassert sorted(keys) == [0, 1, 2, 3, 4]\n",
    ("dict", "extend"): "d = {1: 'a'}\nd.update({2: 'b', 3: 'c'})\nassert d == {1:'a', 2:'b', 3:'c'}\n",
    ("dict", "reverse"): "d = {1: 'a', 2: 'b', 3: 'c'}\nitems = list(d.items())\nassert items == [(1, 'a'), (2, 'b'), (3, 'c')]\n",
    ("dict", "sort"): "d = {3: 'c', 1: 'a', 2: 'b'}\nassert sorted(d.keys()) == [1, 2, 3]\n",
    ("dict", "iterate"): "d = {i: i*i for i in range(10)}\ns = sum(d.values())\nassert s == 285\n",
    ("dict", "mutate_during_iter"): "d = {1: 'a', 2: 'b'}\ncollected = []\nfor k in list(d.keys()):\n    collected.append(k)\n    if k == 2:\n        d[3] = 'c'\nassert collected == [1, 2]\n",
    ("dict", "lookup"): "d = {i: i for i in range(100)}\nassert d.get(50) == 50 and d.get(999) is None\n",
    ("dict", "resize"): "d = {}\nfor i in range(1000):\n    d[i] = i\nassert len(d) == 1000\n",
    ("dict", "hash_collision"): (
        # 1 and 1 << 64 hash-collide under SipHash in some builds; use str
        "d = {'a' + chr(i): i for i in range(10)}\nassert d['a' + chr(0)] == 0\n"
    ),

    ("set", "append"): "s = set()\nfor i in range(100):\n    s.add(i)\nassert len(s) == 100\n",
    ("set", "pop"): "s = {1, 2, 3}\nv = s.pop()\nassert v in (1, 2, 3) and len(s) == 2\n",
    ("set", "insert"): "s = set()\ns.add(1); s.add(2); s.add(1)\nassert s == {1, 2}\n",
    ("set", "remove"): "s = {1, 2, 3}\ns.discard(2)\ns.discard(99)\nassert s == {1, 3}\n",
    ("set", "slice"): "s = set(range(10))\nfirst3 = sorted(s)[:3]\nassert first3 == [0, 1, 2]\n",
    ("set", "extend"): "s = {1, 2}\ns.update({3, 4})\nassert s == {1, 2, 3, 4}\n",
    ("set", "reverse"): "s = {3, 1, 2}\nassert sorted(s) == [1, 2, 3]\n",
    ("set", "sort"): "s = {3, 1, 2}\nassert sorted(s) == [1, 2, 3]\n",
    ("set", "iterate"): "s = set(range(100))\ntotal = sum(s)\nassert total == 4950\n",
    ("set", "mutate_during_iter"): "s = {1, 2, 3}\nfor v in list(s):\n    s.discard(v)\nassert s == set()\n",
    ("set", "lookup"): "s = set(range(100))\nassert 50 in s and 999 not in s\n",
    ("set", "resize"): "s = set()\nfor i in range(1000):\n    s.add(i)\nassert len(s) == 1000\n",
    ("set", "hash_collision"): "s = {1, 2, 3}\nassert s == {3, 2, 1}\n",

    ("tuple", "append"): "t = (1, 2, 3)\nassert t + (4,) == (1, 2, 3, 4)\n",
    ("tuple", "pop"): "t = (1, 2, 3)\nassert t[:-1] == (1, 2)\n",
    ("tuple", "insert"): "t = (1, 2)\nassert (t[0],) + t[1:] == (1, 2)\n",
    ("tuple", "remove"): "t = (1, 2, 3, 2)\nassert tuple(x for x in t if x != 2) == (1, 3)\n",
    ("tuple", "slice"): "t = tuple(range(10))\nassert t[2:5] == (2, 3, 4)\nassert t[::-1] == tuple(range(9, -1, -1))\n",
    ("tuple", "extend"): "t = (1, 2)\nassert t + (3, 4) == (1, 2,3,4)\n",
    ("tuple", "reverse"): "t = (1, 2, 3)\nassert t[::-1] == (3, 2, 1)\n",
    ("tuple", "sort"): "t = (3, 1, 2)\nassert tuple(sorted(t)) == (1, 2, 3)\n",
    ("tuple", "iterate"): "t = tuple(range(100))\nassert sum(t) == 4950\n",
    ("tuple", "mutate_during_iter"): "t = (1, 2, 3)\nseen = []\nfor v in t:\n    seen.append(v)\nassert seen == [1, 2, 3]\n",
    ("tuple", "lookup"): "t = tuple(range(100))\nassert 50 in t and 999 not in t\n",
    ("tuple", "resize"): "t = tuple(range(1000))\nassert len(t) == 1000\n",
    ("tuple", "hash_collision"): "t = (1, 1, 1)\nassert t.count(1) == 3\n",

    ("frozenset", "append"): "s = frozenset(range(100))\nassert len(s) == 100\n",
    ("frozenset", "pop"): "s = frozenset({1, 2, 3})\nassert s == {1, 2, 3}\n",
    ("frozenset", "insert"): "s = frozenset({1, 2}) | {3}\nassert s == {1, 2, 3}\n",
    ("frozenset", "remove"): "s = frozenset({1, 2, 3}) - {2}\nassert s == {1, 3}\n",
    ("frozenset", "slice"): "s = frozenset(range(10))\nassert sorted(s)[:3] == [0, 1, 2]\n",
    ("frozenset", "extend"): "s = frozenset({1, 2}) | {3, 4}\nassert s == {1, 2, 3, 4}\n",
    ("frozenset", "reverse"): "s = frozenset({3, 1, 2})\nassert sorted(s) == [1, 2, 3]\n",
    ("frozenset", "sort"): "s = frozenset({3, 1, 2})\nassert sorted(s) == [1, 2, 3]\n",
    ("frozenset", "iterate"): "s = frozenset(range(100))\nassert sum(s) == 4950\n",
    ("frozenset", "mutate_during_iter"): "s = frozenset({1, 2, 3})\nseen = []\nfor v in s:\n    seen.append(v)\nassert sorted(seen) == [1, 2, 3]\n",
    ("frozenset", "lookup"): "s = frozenset(range(100))\nassert 50 in s and 999 not in s\n",
    ("frozenset", "resize"): "s = frozenset(range(1000))\nassert len(s) == 1000\n",
    ("frozenset", "hash_collision"): "s = frozenset({1, 2, 3})\nassert s == frozenset({3, 2, 1})\n",
}


_ALIAS_SUFFIX = {
    "none": "",
    "shallow": "a = [1, 2]\nb = a\nb.append(3)\nassert a == [1, 2, 3]\n",
    "nested": "a = [[1, 2], [3, 4]]\nb = a[0]\nb.append(99)\nassert a[0] == [1, 2, 99]\n",
    "cyclic": "a = []\nb = [a]\na.append(b)\nassert a[0] is b and b[0] is a\n",
}


def generate(*, n: int = 25_000, seed: int = 0) -> Iterator[TestCase]:
    gb = GridBuilder(category="containers", id_prefix="cont")

    # Build the cartesian product of container/op + aliasing + opt state.
    base = []
    for c in CONTAINERS:
        for op in OPERATIONS:
            key = (c, op)
            if key in _TEMPLATES:
                base.append(key)
    grid = param_grid(base=base, alias=ALIASING, opt=OPT_STATES)

    materialized = list(gb.expand_simple(
        grid,
        lambda p: _TEMPLATES[p["base"]] + "\n" + _ALIAS_SUFFIX[p["alias"]],
        tags_fn=lambda p: TagSet.make(
            "containers",
            type_stability="monomorphic",
            control_flow="loop" if "iterate" in p["base"][1] or "resize" in p["base"][1] else "straight_line",
            call_behavior="direct",
            opt_state=p["opt"].value,
            tags={"container", p["base"][0], p["base"][1], f"alias_{p['alias']}"},
        ),
    ))

    for i in range(n):
        case = materialized[i % len(materialized)]
        yield TestCase(
            source=case.source,
            inputs=case.inputs,
            tags=case.tags,
            id=f"cont-{i:07d}",
            category=case.category,
        )
