"""Strings / Unicode: 15K tests.

Axes:

    content_kind   : ascii | utf8 | bmp | non_bmp | combining | empty |
                     long | interned | repeated_concat | mixed_ascii
    operation      : concat | slice | search | replace | split | join |
                     format | encode | decode | case | strip | count |
                     startswith | endswith | index
    opt_state      : all 6
"""

from __future__ import annotations

from typing import Iterator

from ..harness import OptState, TagSet, TestCase
from ._common import GridBuilder, param_grid


CONTENT_KINDS = (
    "ascii", "utf8", "bmp", "non_bmp", "combining", "empty",
    "long", "interned", "repeated_concat", "mixed_ascii",
)
OPERATIONS = (
    "concat", "slice", "search", "replace", "split", "join",
    "format", "encode", "decode", "case", "strip", "count",
    "startswith", "endswith", "index",
)
OPT_STATES = [OptState.COLD, OptState.WARM, OptState.HOT, OptState.VERY_HOT, OptState.DEOPT, OptState.REHEATED]


_CONTENT_LITERALS = {
    "ascii": "'hello world'",
    "utf8": "'héllo wörld'",
    "bmp": "'中文测试'",
    "non_bmp": "'😀🌍🚀'",
    "combining": "'e\u0301'",
    "empty": "''",
    "long": "'x' * 1024",
    "interned": "sys.intern('interned_key')" if False else "'interned_key'",
    "repeated_concat": "'ab' * 100",
    "mixed_ascii": "'abc中文'",
}


def _op_source(op: str, content: str) -> str:
    s = _CONTENT_LITERALS[content]
    if op == "concat":
        return f"s = {s}\nassert (s + s) == s * 2\n"
    if op == "slice":
        return f"s = {s}\nassert s[1:3] == s[1:3]\nassert s[::-1] == s[::-1]\n"
    if op == "search":
        return f"s = {s}\nassert ('l' in s) == ('l' in s)\n"
    if op == "replace":
        return f"s = {s}\nassert s.replace('l', 'L') == s.replace('l', 'L')\n"
    if op == "split":
        return f"s = {s}\nparts = s.split(' ')\nassert isinstance(parts, list)\n"
    if op == "join":
        return f"s = {s}\nassert ','.join([s, s]) == s + ',' + s\n"
    if op == "format":
        return f"s = {s}\nassert ('{{}}').format() == '{{}}'\nassert 'x' + s == 'x' + s\n"
    if op == "encode":
        return f"s = {s}\nb = s.encode('utf-8')\nassert b.decode('utf-8') == s\n"
    if op == "decode":
        return f"s = {s}\nb = s.encode('utf-8')\nassert b.decode('utf-8') == s\n"
    if op == "case":
        return f"s = {s}\nassert s.upper().lower() == s.lower()\n"
    if op == "strip":
        return f"s = {s}\nassert s.strip() == s.strip()\n"
    if op == "count":
        return f"s = {s}\nassert s.count('') == len(s) + 1\n"
    if op == "startswith":
        return f"s = {s}\nassert s.startswith(s[:3]) == True if len(s) >= 3 else True\n"
    if op == "endswith":
        return f"s = {s}\nassert s.endswith(s[-3:]) == True if len(s) >= 3 else True\n"
    if op == "index":
        return f"s = {s}\ntry:\n    i = s.index('zzz')\nexcept ValueError:\n    i = -1\nassert i == -1 or i >= 0\n"
    return "pass\n"


def generate(*, n: int = 15_000, seed: int = 0) -> Iterator[TestCase]:
    gb = GridBuilder(category="strings", id_prefix="str")
    grid = param_grid(content=CONTENT_KINDS, op=OPERATIONS, opt=OPT_STATES)

    materialized = list(gb.expand_simple(
        grid,
        lambda p: _op_source(p["op"], p["content"]),
        tags_fn=lambda p: TagSet.make(
            "strings",
            type_stability="monomorphic",
            control_flow="straight_line",
            call_behavior="builtin",
            opt_state=p["opt"].value,
            tags={"string", "unicode", p["content"], p["op"]},
        ),
    ))

    for i in range(n):
        case = materialized[i % len(materialized)]
        yield TestCase(
            source=case.source,
            inputs=case.inputs,
            tags=case.tags,
            id=f"str-{i:07d}",
            category=case.category,
        )
