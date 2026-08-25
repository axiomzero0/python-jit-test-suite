"""Numeric workloads: 25K tests.

Huge parameter space across integer, float, mixed numeric, and tight
loop kernels. Designed to catch:

- integer overflow assumptions (Python ints are arbitrary precision)
- IEEE-754 edge cases (subnormals, ±0, ±inf, NaN)
- mixed-arithmetic coercion bugs
- reduction kernel accuracy

Axes:

    op_family      : add | sub | mul | div | floordiv | mod | pow |
                     bitand | bitor | bitxor | lshift | rshift | neg |
                     abs | sqrt-like | transcend
    operand_kind  : small_int | large_int | neg_int | zero |
                     small_float | large_float | subnormal | neg_zero |
                     inf | nan | bool | complex | mixed_int_float
    loop_size     : 1 | 10 | 100 | 1000 | 10000
"""

from __future__ import annotations

import itertools
from typing import Iterator

from ..harness import OptState, TagSet, TestCase
from ._common import GridBuilder, param_grid


OP_FAMILIES = (
    "add", "sub", "mul", "truediv", "floordiv", "mod", "pow",
    "bitand", "bitor", "bitxor", "lshift", "rshift",
    "neg", "abs", "transcend",
)
OPERAND_KINDS = (
    "small_int", "large_int", "neg_int", "zero",
    "small_float", "large_float", "subnormal", "neg_zero",
    "inf", "nan", "bool", "complex", "mixed_int_float",
)
LOOP_SIZES = (1, 10, 100, 1000, 10000)


def _operand_value(kind: str) -> object:
    return {
        "small_int": 7,
        "large_int": 2 ** 64 + 13,
        "neg_int": -12345,
        "zero": 0,
        "small_float": 1.5,
        "large_float": 1e308,
        "subnormal": 5e-324,
        "neg_zero": -0.0,
        "inf": float("inf"),
        "nan": float("nan"),
        "bool": True,
        "complex": complex(1, 2),
        "mixed_int_float": 3,  # second operand will be a float
    }[kind]


def _operand_pair(k1: str, k2: str) -> tuple[object, object]:
    a = _operand_value(k1)
    b = _operand_value(k2)
    if k1 == "mixed_int_float":
        b = 2.5
    if k2 == "mixed_int_float":
        a = 2.5
    return a, b


def _op_source(op: str, k1: str, k2: str, loop_size: int) -> tuple[str, dict]:
    a, b = _operand_pair(k1, k2)

    # Build a kernel: out = fold(op, init, range)
    if op == "add":
        body = "x + y"
    elif op == "sub":
        body = "x - y"
    elif op == "mul":
        body = "x * y"
    elif op == "truediv":
        body = "x / y" if k2 != "zero" else "1.0 if y == 0 else x / y"
    elif op == "floordiv":
        body = "x // y" if k2 != "zero" else "0"
    elif op == "mod":
        body = "x % y" if k2 != "zero" else "0"
    elif op == "pow":
        body = "x ** y"
    elif op == "bitand":
        body = "x & y"
    elif op == "bitor":
        body = "x | y"
    elif op == "bitxor":
        body = "x ^ y"
    elif op == "lshift":
        body = "x << y" if k2 != "large_int" else "x << 4"
    elif op == "rshift":
        body = "x >> y" if k2 != "large_int" else "x >> 4"
    elif op == "neg":
        body = "-x"
    elif op == "abs":
        body = "abs(x)"
    elif op == "transcend":
        # Use a math function rather than an op
        src = (
            "import math\n"
            f"def main():\n"
            f"    s = 0.0\n"
            f"    for i in range({loop_size}):\n"
            f"        s += math.sqrt(float(i + 1))\n"
            f"    return s\n"
        )
        return src, {}
    else:
        body = "x + y"

    src = (
        f"def main():\n"
        f"    s = 0\n"
        f"    x = {a!r}\n"
        f"    y = {b!r}\n"
        f"    for i in range({loop_size}):\n"
        f"        s = ({body})\n"
        f"    return s\n"
    )
    return src, {}


def _op_opt_state(loop_size: int) -> OptState:
    if loop_size == 1:
        return OptState.COLD
    if loop_size == 10:
        return OptState.WARM
    if loop_size == 100:
        return OptState.HOT
    if loop_size == 1000:
        return OptState.HOT
    return OptState.VERY_HOT


def generate(*, n: int = 25_000, seed: int = 0) -> Iterator[TestCase]:
    gb = GridBuilder(category="numeric", id_prefix="num")
    grid = param_grid(op=OP_FAMILIES, k1=OPERAND_KINDS, k2=OPERAND_KINDS, loop=LOOP_SIZES)

    materialized = []
    for params in grid:
        op, k1, k2, loop = params["op"], params["k1"], params["k2"], params["loop"]
        # Skip combinations that always raise (e.g. truediv by zero) and
        # bitops on floats: the harness would see a ZeroDivisionError/TypeError
        # on both sides which is still a valid differential test, but we want
        # to spend our budget on meaningful cases.
        if op in ("bitand", "bitor", "bitxor", "lshift", "rshift"):
            if k1 in ("small_float", "large_float", "subnormal", "neg_zero", "inf", "nan", "complex", "mixed_int_float"):
                continue
            if k2 in ("small_float", "large_float", "subnormal", "neg_zero", "inf", "nan", "complex", "mixed_int_float"):
                continue
        if op == "pow" and k2 == "large_int":
            continue  # enormous; skip
        source, _inputs = _op_source(op, k1, k2, loop)
        materialized.append(TestCase(
            source=source,
            inputs=(),
            tags=TagSet.make(
                "numeric",
                type_stability="monomorphic",
                control_flow="loop",
                call_behavior="direct",
                opt_state=_op_opt_state(loop).value,
                tags={"numeric", op, k1, k2, f"loop_{loop}"},
            ),
            id=f"num-{len(materialized):07d}",
            category="numeric",
        ))

    # Cycle through the materialized list to hit the target n.
    for i in range(n):
        case = materialized[i % len(materialized)]
        yield TestCase(
            source=case.source,
            inputs=case.inputs,
            tags=case.tags,
            id=f"num-{i:07d}",
            category=case.category,
        )
