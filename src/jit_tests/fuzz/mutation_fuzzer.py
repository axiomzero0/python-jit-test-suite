"""Mutation fuzzer: take seed programs and mutate them.

Mutations:
    - operator replacement      (+  ->  -, *, /, //, %)
    - constant replacement       (5  ->  0, 1, -1, large, float, NaN)
    - variable swap              (x  ->  y, z)
    - branch flip                (if x  ->  if not x)
    - loop bound mutation        (range(10)  ->  range(0), range(100))
    - call target swap           (len -> abs, max, min, sum)
    - container type swap        ([...]  ->  (...), {...})
    - attribute swap             (.x  ->  .y)
    - exception type swap        (ValueError  ->  KeyError, TypeError)

Seeds: a small library of canonical snippets that cover the main axes
(monkey-patched here for reuse). The mutation pipeline runs each seed
through N random mutations, producing N children per seed.
"""

from __future__ import annotations

import ast
import random
import re
from typing import Iterator

from ..harness import OptState, TagSet, TestCase


_SEEDS = [
    # numeric reductions
    "def main():\n    s = 0\n    for i in range(10):\n        s += i * 2\n    return s\n",
    "def main():\n    x = 1\n    for i in range(5):\n        x = x + i\n    return x\n",
    "def main():\n    a = [1, 2, 3, 4]\n    return sum(a)\n",
    # container iteration
    "def main():\n    d = {i: i*i for i in range(5)}\n    return d[2] + d[3]\n",
    "def main():\n    s = set()\n    for i in range(10):\n        s.add(i % 3)\n    return len(s)\n",
    # branching
    "def main():\n    x = 5\n    if x > 3:\n        return x * 2\n    else:\n        return x\n",
    # exception handling
    "def main():\n    try:\n        x = 1 / 0\n    except ZeroDivisionError:\n        return -1\n    return x\n",
    "def main():\n    s = 0\n    for i in range(10):\n        try:\n            if i == 5:\n                raise ValueError()\n            s += i\n        except ValueError:\n            s -= 1\n    return s\n",
    # recursion
    "def main():\n    def f(n):\n        if n <= 1:\n            return 1\n        return n * f(n - 1)\n    return f(5)\n",
    # closures
    "def main():\n    def make(x):\n        def f(y):\n            return x + y\n        return f\n    add5 = make(5)\n    return add5(3)\n",
    # generator
    "def main():\n    def g(n):\n        for i in range(n):\n            yield i * i\n    return list(g(5))\n",
    # string ops
    "def main():\n    s = 'hello world'\n    return s.replace('l', 'L').upper()\n",
    "def main():\n    s = 'abc,def,ghi'\n    parts = s.split(',')\n    return len(parts)\n",
]


_BIN_OP_MUTATIONS = {
    ast.Add: [ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow, ast.BitAnd, ast.BitOr],
    ast.Sub: [ast.Add, ast.Mult, ast.Div],
    ast.Mult: [ast.Add, ast.Sub, ast.Div, ast.Pow],
    ast.Div: [ast.FloorDiv, ast.Mult],
    ast.FloorDiv: [ast.Div, ast.Mod],
    ast.Mod: [ast.FloorDiv],
    ast.Pow: [ast.Mult],
    ast.BitAnd: [ast.BitOr, ast.BitXor],
    ast.BitOr: [ast.BitAnd, ast.BitXor],
    ast.BitXor: [ast.BitAnd, ast.BitOr],
}
_CONST_MUTATIONS = [0, 1, -1, 2, 7, 100, 2**31, 0.0, 1.5, -1.0, "", "x", True, False, None, 1.0e10]
_NAME_MUTATIONS = {
    "x": ["y", "z"], "y": ["x", "z"], "z": ["x", "y"],
    "len": ["abs", "max", "min", "sum"], "abs": ["len", "max"],
    "max": ["min", "abs"], "min": ["max", "abs"], "sum": ["len"],
}


class _Mutator(ast.NodeTransformer):
    def __init__(self, rng: random.Random) -> None:
        self.rng = rng
        self.mutation_count = 0

    def visit_BinOp(self, node):
        self.generic_visit(node)
        if type(node.op) in _BIN_OP_MUTATIONS and self.rng.random() < 0.3:
            new_op_cls = self.rng.choice(_BIN_OP_MUTATIONS[type(node.op)])
            node.op = new_op_cls()
            self.mutation_count += 1
        return node

    def visit_Constant(self, node):
        if self.rng.random() < 0.3:
            node.value = self.rng.choice(_CONST_MUTATIONS)
            self.mutation_count += 1
        return node

    def visit_Name(self, node):
        if node.id in _NAME_MUTATIONS and self.rng.random() < 0.2:
            node.id = self.rng.choice(_NAME_MUTATIONS[node.id])
            self.mutation_count += 1
        return node

    def visit_Compare(self, node):
        self.generic_visit(node)
        if self.rng.random() < 0.2 and node.ops:
            # flip equality / inequality
            op = node.ops[0]
            if isinstance(op, ast.Eq):
                node.ops[0] = ast.NotEq()
                self.mutation_count += 1
            elif isinstance(op, ast.NotEq):
                node.ops[0] = ast.Eq()
                self.mutation_count += 1
            elif isinstance(op, ast.Lt):
                node.ops[0] = ast.GtE()
                self.mutation_count += 1
            elif isinstance(op, ast.Gt):
                node.ops[0] = ast.LtE()
                self.mutation_count += 1
        return node

    def visit_For(self, node):
        self.generic_visit(node)
        if self.rng.random() < 0.3 and isinstance(node.iter, ast.Call):
            # mutate range bounds
            call = node.iter
            if isinstance(call.func, ast.Name) and call.func.id == "range":
                if call.args and isinstance(call.args[0], ast.Constant):
                    call.args[0] = ast.Constant(self.rng.choice([0, 1, 5, 100, 1000]))
                    self.mutation_count += 1
        return node


def mutate(source: str, rng: random.Random) -> tuple[str, int]:
    """Return (mutated_source, n_mutations). Always returns a compilable program
    (falls back to the original if mutation produced invalid source)."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return source, 0
    mutator = _Mutator(rng)
    new_tree = mutator.visit(tree)
    if mutator.mutation_count == 0:
        return source, 0
    try:
        ast.fix_missing_locations(new_tree)
        new_src = ast.unparse(new_tree)
        compile(new_src, "<mut>", "exec")
        return new_src, mutator.mutation_count
    except Exception:
        return source, 0


def generate(*, n: int = 250_000, seed: int = 0) -> Iterator[TestCase]:
    rng = random.Random(seed)
    for i in range(n):
        seed_src = rng.choice(_SEEDS)
        mutated, n_mut = mutate(seed_src, rng)
        opt = rng.choices(
            [OptState.COLD, OptState.WARM, OptState.HOT, OptState.DEOPT],
            weights=[4, 3, 2, 1], k=1)[0]
        yield TestCase(
            source=mutated,
            inputs=(),
            tags=TagSet.make(
                "language_semantics",
                type_stability="unknown",
                control_flow="loop",
                call_behavior="direct",
                opt_state=opt.value,
                tags={"fuzz", "mutation", f"mutations_{n_mut}"},
            ),
            id=f"fuzz-mut-{i:08d}",
            category="fuzz_mutation",
        )
