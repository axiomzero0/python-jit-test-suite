"""Minimizer: delta-debug a failing fuzz case down to the smallest input
that still fails.

Algorithm: classic ddmin (delta debugging). Given a program represented
as a list of AST nodes (or a sequence of statements), repeatedly halve
the input and keep the smallest subset that still triggers the failure.

We minimize along two axes:

1. Statement removal (drop statements that aren't needed to trigger)
2. Constant folding (replace constants with smaller ones if behavior
   preserved as a failure)

Output: a minimized source string + a report describing what was removed.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Callable

from ..harness import TestCase
from ..harness.oracle import Observation, compare, run_cpython


@dataclass
class MinimizeReport:
    original_source: str
    minimized_source: str
    original_node_count: int
    minimized_node_count: int
    rounds: int


def _node_count(src: str) -> int:
    try:
        return sum(1 for _ in ast.walk(ast.parse(src)))
    except SyntaxError:
        return -1


def _still_fails(
    src: str,
    *,
    inputs: dict,
    expected: Observation,
    runner_fn: Callable[[str, dict], Observation],
) -> bool:
    try:
        compile(src, "<min>", "exec")
    except SyntaxError:
        return False
    obs = runner_fn(src, inputs)
    ok, _ = compare(expected, obs)
    return not ok  # If comparison fails, we still reproduce the bug


def ddmin_statements(
    src: str,
    *,
    inputs: dict,
    expected: Observation,
    runner_fn: Callable[[str, dict], Observation],
    max_rounds: int = 20,
) -> str:
    """Delta-debug the top-level statements of a module body."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return src

    body = list(tree.body)
    if len(body) <= 1:
        return src

    n = len(body)
    granularity = 2
    rounds = 0

    while granularity <= n and rounds < max_rounds:
        rounds += 1
        chunk = max(1, n // granularity)
        reduced = False
        for start in range(0, n, chunk):
            end = start + chunk
            subset = body[:start] + body[end:]
            new_tree = ast.Module(body=subset, type_ignores=[])
            try:
                ast.fix_missing_locations(new_tree)
                new_src = ast.unparse(new_tree)
            except Exception:
                continue
            if _still_fails(new_src, inputs=inputs, expected=expected, runner_fn=runner_fn):
                body = subset
                n = len(body)
                tree = ast.Module(body=body, type_ignores=[])
                reduced = True
                break
        if not reduced:
            granularity *= 2

    try:
        ast.fix_missing_locations(tree)
        return ast.unparse(tree)
    except Exception:
        return src


def minimize_constants(
    src: str,
    *,
    inputs: dict,
    expected: Observation,
    runner_fn: Callable[[str, dict], Observation],
) -> str:
    """Replace constants with smaller equivalents if the failure still reproduces."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return src

    replacements = {0: 0, 1: 1, -1: -1, 100: 1, 1000: 1, 2 ** 31: 1, 2 ** 64: 1}

    class _ConstShrinker(ast.NodeTransformer):
        def visit_Constant(self, node):
            if isinstance(node.value, int) and abs(node.value) > 2:
                if _still_fails(
                    ast.unparse(_replace_in_tree(tree, node, ast.Constant(2))),
                    inputs=inputs,
                    expected=expected,
                    runner_fn=runner_fn,
                ):
                    return ast.Constant(2)
            return node

    new_tree = _ConstShrinker().visit(tree)
    try:
        ast.fix_missing_locations(new_tree)
        return ast.unparse(new_tree)
    except Exception:
        return src


def _replace_in_tree(tree: ast.AST, old_node: ast.AST, new_node: ast.AST) -> ast.AST:
    """Return a deep copy of ``tree`` with ``old_node`` replaced by ``new_node``."""
    import copy

    class _Replacer(ast.NodeTransformer):
        def visit(self, node):
            if node is old_node:
                return copy.deepcopy(new_node)
            return self.generic_visit(node)

    return _Replacer().visit(copy.deepcopy(tree))


def minimize(
    case: TestCase,
    *,
    expected: Observation,
    runner_fn: Callable[[str, dict], Observation] | None = None,
) -> MinimizeReport:
    """Minimize a failing fuzz case.

    ``runner_fn`` defaults to running under CPython reference. If you're
    using a custom JIT candidate, pass a function that runs the source
    through the JIT and returns an :class:`Observation`.
    """
    if runner_fn is None:
        def runner_fn(src: str, inputs: dict) -> Observation:
            return run_cpython(src, inputs=inputs)

    orig_src = case.source
    orig_nodes = _node_count(orig_src)

    min1 = ddmin_statements(
        orig_src,
        inputs=case.inputs_dict,
        expected=expected,
        runner_fn=runner_fn,
    )
    min2 = minimize_constants(
        min1,
        inputs=case.inputs_dict,
        expected=expected,
        runner_fn=runner_fn,
    )

    final_nodes = _node_count(min2)
    return MinimizeReport(
        original_source=orig_src,
        minimized_source=min2,
        original_node_count=orig_nodes,
        minimized_node_count=final_nodes,
        rounds=1,
    )
