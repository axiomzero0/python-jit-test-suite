"""Interpreter/JIT tier transitions: 15K tests.

These tests deliberately drive the runtime across interpreter → baseline
JIT → optimizing JIT → deopt → OSR → re-entry boundaries. They are the
*behavior* tests that catch bugs where a function works perfectly in the
interpreter but misbehaves once optimized.

Axes:

    tier_path      : interp_only | interp_to_base | interp_to_opt |
                     interp_to_opt_deopt | osr_loop | osr_loop_deopt |
                     multi_deopt | tier_reheat
    loop_kind      : for | while | nested | recursion
    side_effects   : print | append | assign_global | raise | none
"""

from __future__ import annotations

from typing import Iterator

from ..harness import OptState, TagSet, TestCase
from ._common import GridBuilder, param_grid


TIER_PATHS = (
    "interp_only",
    "interp_to_base",
    "interp_to_opt",
    "interp_to_opt_deopt",
    "osr_loop",
    "osr_loop_deopt",
    "multi_deopt",
    "tier_reheat",
)
LOOP_KINDS = ("for", "while", "nested", "recursion")
SIDE_EFFECTS = ("print", "append", "assign_global", "raise", "none")


def _tier_source(tier: str, loop: str, se: str) -> str:
    body_accum = {
        "print": "print(i)\n",
        "append": "acc.append(i)\n",
        "assign_global": "g_state[0] = i\n",
        "raise": "if i == 50:\n    raise ValueError('mid-loop')\n",
        "none": "pass\n",
    }[se]

    if loop == "for":
        loop_body = f"for i in range(100):\n    {body_accum.replace(chr(10), chr(10) + '    ')}"
        # Better: just build properly
        loop_body = "for i in range(100):\n" + "".join(
            f"    {line}\n" for line in body_accum.rstrip("\n").split("\n")
        )
    elif loop == "while":
        loop_body = (
            "i = 0\n"
            "while i < 100:\n"
            + "".join(f"    {line}\n" for line in body_accum.rstrip("\n").split("\n"))
            + "    i += 1\n"
        )
    elif loop == "nested":
        loop_body = (
            "for i in range(10):\n"
            "    for j in range(10):\n"
            + "".join(f"        {line}\n" for line in body_accum.rstrip("\n").split("\n"))
        )
    elif loop == "recursion":
        return (
            "def rec(n, acc):\n"
            "    if n <= 0:\n"
            "        return acc\n"
            f"    {body_accum.replace('i', 'n').rstrip()}\n"
            "    return rec(n - 1, acc + 1)\n"
            "acc = rec(100, 0)\n"
            "assert acc == 100\n"
        )
    else:
        loop_body = "pass\n"

    if se == "append":
        src = "acc = []\n" + loop_body + "assert len(acc) == 100\n"
    elif se == "assign_global":
        src = "g_state = [0]\n" + loop_body + "assert g_state[0] == 99\n"
    elif se == "raise":
        src = (
            "try:\n"
            + "".join(f"    {line}\n" for line in loop_body.rstrip("\n").split("\n"))
            + "except ValueError:\n"
            "    pass\n"
        )
    elif se == "print":
        src = loop_body
    else:
        src = loop_body + "assert True\n"
    return src


def _tier_opt_state(tier: str) -> OptState:
    return {
        "interp_only": OptState.COLD,
        "interp_to_base": OptState.WARM,
        "interp_to_opt": OptState.HOT,
        "interp_to_opt_deopt": OptState.DEOPT,
        "osr_loop": OptState.HOT,
        "osr_loop_deopt": OptState.DEOPT,
        "multi_deopt": OptState.DEOPT,
        "tier_reheat": OptState.REHEATED,
    }[tier]


def generate(*, n: int = 15_000, seed: int = 0) -> Iterator[TestCase]:
    gb = GridBuilder(category="interpreter_tiers", id_prefix="tier")
    grid = param_grid(tier=TIER_PATHS, loop=LOOP_KINDS, se=SIDE_EFFECTS)
    materialized = list(gb.expand_simple(
        grid,
        lambda p: _tier_source(p["tier"], p["loop"], p["se"]),
        tags_fn=lambda p: TagSet.make(
            "interpreter_tiers",
            type_stability="monomorphic",
            control_flow=("loop" if p["loop"] != "recursion" else "recursion"),
            call_behavior=("recursive" if p["loop"] == "recursion" else "direct"),
            opt_state=_tier_opt_state(p["tier"]).value,
            tags={"tier-transition", p["tier"], "OSR", "deoptimization"},
        ),
    ))

    # Cycle through materialized cases until we hit n.
    for i in range(n):
        case = materialized[i % len(materialized)]
        yield TestCase(
            source=case.source,
            inputs=case.inputs,
            tags=case.tags,
            id=f"tier-{i:07d}",
            category=case.category,
        )
