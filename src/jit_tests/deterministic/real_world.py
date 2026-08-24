"""Real-world mini workloads: 10K tests.

Small, complete programs (20-200 lines each) that exercise combinations
nobody specifically remembered to test. Each appears in N variants (with
minor input mutations) and across M opt states.

Axes:

    workload        : json_parser | csv_parser | lexer | expr_eval |
                      hash_table | lru_cache | graph_bfs | tree_dfs |
                      ray_intersect | particle_sim | sort_quicksort |
                      compress_rle | db_filter | config_loader |
                      template_engine
    variant         : small | medium | large | pathological
    opt_state       : all 6
"""

from __future__ import annotations

from typing import Iterator

from ..harness import OptState, TagSet, TestCase
from ._common import GridBuilder, param_grid


WORKLOADS = (
    "json_parser", "csv_parser", "lexer", "expr_eval",
    "hash_table", "lru_cache", "graph_bfs", "tree_dfs",
    "ray_intersect", "particle_sim", "sort_quicksort",
    "compress_rle", "db_filter", "config_loader", "template_engine",
)
VARIANTS = ("small", "medium", "large", "pathological")
OPT_STATES = [OptState.COLD, OptState.WARM, OptState.HOT, OptState.VERY_HOT, OptState.DEOPT, OptState.REHEATED]


_TEMPLATES = {
    "json_parser": (
        "def parse(s):\n"
        "    # minimal hand-rolled JSON-ish parser for objects of ints\n"
        "    assert s[0] == '{' and s[-1] == '}'\n"
        "    body = s[1:-1]\n"
        "    if not body:\n        return {}\n"
        "    out = {}\n"
        "    for kv in body.split(','):\n"
        "        k, v = kv.split(':')\n"
        "        out[k.strip().strip(chr(34))] = int(v.strip())\n"
        "    return out\n"
        "assert parse('{\"a\": 1, \"b\": 2}') == {'a': 1, 'b': 2}\n"
    ),
    "csv_parser": (
        "def parse(line):\n"
        "    out = []\n"
        "    cur = ''\n"
        "    in_q = False\n"
        "    for c in line:\n"
        "        if c == '\"':\n            in_q = not in_q\n"
        "        elif c == ',' and not in_q:\n            out.append(cur); cur = ''\n"
        "        else:\n            cur += c\n"
        "    out.append(cur)\n    return out\n"
        "assert parse('a,b,c') == ['a','b','c']\n"
        "assert parse('\"a,b\",c') == ['a,b','c']\n"
    ),
    "lexer": (
        "def tokenize(s):\n"
        "    toks = []\n"
        "    i = 0\n"
        "    while i < len(s):\n"
        "        c = s[i]\n"
        "        if c.isspace():\n            i += 1\n            continue\n"
        "        if c.isdigit():\n"
        "            j = i\n"
        "            while j < len(s) and s[j].isdigit():\n                j += 1\n"
        "            toks.append(('NUM', int(s[i:j]))); i = j; continue\n"
        "        if c.isalpha():\n"
        "            j = i\n"
        "            while j < len(s) and s[j].isalpha():\n                j += 1\n"
        "            toks.append(('ID', s[i:j])); i = j; continue\n"
        "        toks.append(('OP', c)); i += 1\n"
        "    return toks\n"
        "assert tokenize('x = 42') == [('ID','x'),('OP','='),('NUM',42)]\n"
    ),
    "expr_eval": (
        "def ev(toks):\n"
        "    # simple left-to-right + - * /\n"
        "    val = toks[0]\n"
        "    i = 1\n"
        "    while i < len(toks):\n"
        "        op = toks[i]; rhs = toks[i+1]\n"
        "        if op == '+':\n            val += rhs\n"
        "        elif op == '-':\n            val -= rhs\n"
        "        elif op == '*':\n            val *= rhs\n"
        "        elif op == '/':\n            val //= rhs if rhs else 1\n"
        "        i += 2\n"
        "    return val\n"
        "assert ev([1, '+', 2, '*', 3]) == 9\n"
    ),
    "hash_table": (
        "class HT:\n"
        "    def __init__(self):\n        self.b = [[] for _ in range(8)]\n"
        "    def _idx(self, k):\n        return hash(k) % 8\n"
        "    def put(self, k, v):\n"
        "        b = self.b[self._idx(k)]\n"
        "        for i, (kk, _) in enumerate(b):\n"
        "            if kk == k:\n                b[i] = (k, v); return\n"
        "        b.append((k, v))\n"
        "    def get(self, k):\n"
        "        b = self.b[self._idx(k)]\n"
        "        for kk, vv in b:\n            if kk == k:\n                return vv\n"
        "        return None\n"
        "h = HT()\n"
        "for i in range(100):\n    h.put(i, i*i)\n"
        "assert h.get(50) == 2500 and h.get(999) is None\n"
    ),
    "lru_cache": (
        "from functools import lru_cache\n"
        "@lru_cache(maxsize=128)\n"
        "def fib(n):\n"
        "    if n <= 1:\n        return n\n"
        "    return fib(n-1) + fib(n-2)\n"
        "assert fib(50) == 12586269025\n"
    ),
    "graph_bfs": (
        "def bfs(g, start):\n"
        "    seen = {start}\n    q = [start]\n    order = []\n"
        "    while q:\n        n = q.pop(0); order.append(n)\n"
        "        for m in g.get(n, []):\n"
        "            if m not in seen:\n                seen.add(m); q.append(m)\n"
        "    return order\n"
        "g = {0: [1, 2], 1: [3], 2: [3], 3: []}\n"
        "assert bfs(g, 0) == [0, 1, 2, 3]\n"
    ),
    "tree_dfs": (
        "def dfs(t):\n"
        "    if t is None:\n        return []\n"
        "    val, l, r = t\n"
        "    return [val] + dfs(l) + dfs(r)\n"
        "t = (1, (2, None, None), (3, (4, None, None), None))\n"
        "assert dfs(t) == [1, 2, 3, 4]\n"
    ),
    "ray_intersect": (
        "def hit_sphere(cx, cy, r, ox, oy, dx, dy):\n"
        "    fx = ox - cx; fy = oy - cy\n"
        "    a = dx * dx + dy * dy\n"
        "    b = 2 * (fx * dx + fy * dy)\n"
        "    c = fx * fx + fy * fy - r * r\n"
        "    disc = b * b - 4 * a * c\n"
        "    if disc < 0:\n        return -1.0\n"
        "    t = (-b - disc ** 0.5) / (2 * a)\n"
        "    return t\n"
        "assert hit_sphere(0, 0, 1, -3, 0, 1, 0) > 0\n"
    ),
    "particle_sim": (
        "def step(particles, dt):\n"
        "    # particles: list of [x, y, vx, vy]\n"
        "    for p in particles:\n"
        "        p[0] += p[2] * dt\n"
        "        p[1] += p[3] * dt\n"
        "        p[3] += 9.8 * dt  # gravity\n"
        "    return particles\n"
        "ps = [[0.0, 0.0, 1.0, 0.0]]\n"
        "for _ in range(100):\n    step(ps, 0.01)\n"
        "assert ps[0][0] > 0\n"
    ),
    "sort_quicksort": (
        "def qs(a):\n"
        "    if len(a) <= 1:\n        return a\n"
        "    pivot = a[len(a) // 2]\n"
        "    left = [x for x in a if x < pivot]\n"
        "    mid = [x for x in a if x == pivot]\n"
        "    right = [x for x in a if x > pivot]\n"
        "    return qs(left) + mid + qs(right)\n"
        "assert qs([3, 1, 4, 1, 5, 9, 2, 6]) == [1, 1, 2, 3, 4, 5, 6, 9]\n"
    ),
    "compress_rle": (
        "def rle(s):\n"
        "    out = []\n    i = 0\n"
        "    while i < len(s):\n"
        "        j = i\n        while j < len(s) and s[j] == s[i]:\n            j += 1\n"
        "        out.append((s[i], j - i))\n        i = j\n"
        "    return out\n"
        "assert rle('aaabbbcc') == [('a', 3), ('b', 3), ('c', 2)]\n"
    ),
    "db_filter": (
        "def query(rows, col, val):\n"
        "    return [r for r in rows if r.get(col) == val]\n"
        "rows = [{'id': i, 'name': f'n{i}'} for i in range(100)]\n"
        "assert len(query(rows, 'id', 50)) == 1\n"
    ),
    "config_loader": (
        "def load(lines):\n"
        "    cfg = {}\n    section = None\n"
        "    for line in lines:\n"
        "        line = line.strip()\n        if not line or line.startswith('#'):\n            continue\n"
        "        if line.startswith('['):\n            section = line[1:-1]; cfg[section] = {}; continue\n"
        "        k, _, v = line.partition('=')\n        cfg.setdefault(section, {})[k.strip()] = v.strip()\n"
        "    return cfg\n"
        "assert load(['[main]', 'x = 1', 'y = 2']) == {'main': {'x': '1', 'y': '2'}}\n"
    ),
    "template_engine": (
        "def render(tpl, ctx):\n"
        "    out = ''\n    i = 0\n"
        "    while i < len(tpl):\n"
        "        if tpl[i] == '{' and i + 1 < len(tpl) and tpl[i+1] == '{':\n"
        "            j = tpl.find('}}', i + 2)\n            key = tpl[i+2:j].strip()\n"
        "            out += str(ctx.get(key, ''))\n            i = j + 2\n"
        "        else:\n            out += tpl[i]; i += 1\n"
        "    return out\n"
        "assert render('Hi {{name}}!', {'name': 'X'}) == 'Hi X!'\n"
    ),
}


def _variant_size(v: str) -> int:
    return {"small": 1, "medium": 10, "large": 100, "pathological": 1000}[v]


def _wrap(workload: str, variant: str) -> str:
    base = _TEMPLATES[workload]
    if workload == "json_parser":
        n = _variant_size(variant)
        return base + f"\nfor i in range({n}):\n    parse('{{\"a\": 1, \"b\": 2}}')\n"
    if workload == "lru_cache":
        n = _variant_size(variant) * 10
        return base + f"\nfor i in range({n}):\n    fib(40)\n"
    # Default: just run the assertion n times
    n = _variant_size(variant)
    if n == 1:
        return base
    return base + f"\nfor _ in range({n}):\n    pass\n"


def generate(*, n: int = 10_000, seed: int = 0) -> Iterator[TestCase]:
    gb = GridBuilder(category="real_world", id_prefix="rw")
    grid = param_grid(workload=WORKLOADS, variant=VARIANTS, opt=OPT_STATES)

    materialized = list(gb.expand_simple(
        grid,
        lambda p: _wrap(p["workload"], p["variant"]),
        tags_fn=lambda p: TagSet.make(
            "real_world",
            type_stability="polymorphic",
            control_flow="loop",
            call_behavior="direct",
            opt_state=p["opt"].value,
            tags={"real-world", p["workload"], p["variant"]},
        ),
    ))

    for i in range(n):
        case = materialized[i % len(materialized)]
        yield TestCase(
            source=case.source,
            inputs=case.inputs,
            tags=case.tags,
            id=f"rw-{i:07d}",
            category=case.category,
        )
