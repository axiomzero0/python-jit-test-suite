"""AST fuzzer: generate valid Python ASTs and unparse them to source.

We generate small ASTs with weighted node selection so we don't end up
with 99% literal-only programs. The generator is parameterized by depth
and max nodes; it prefers operators, control flow, and function calls
that have higher "bug-finding value".

Output programs always have a `main()` function so the harness can
capture a return value as the oracle.
"""

from __future__ import annotations

import ast
import random
from typing import Iterator

from ..harness import OptState, TagSet, TestCase


# Weighted node pool. Higher weight = more likely to be generated.
# Operators / control-flow / calls are weighted higher than literals
# because they exercise JIT code paths.
_BIN_OPS = [
    (ast.Add, 8), (ast.Sub, 6), (ast.Mult, 6), (ast.Div, 4),
    (ast.FloorDiv, 3), (ast.Mod, 3), (ast.Pow, 2),
    (ast.BitAnd, 2), (ast.BitOr, 2), (ast.BitXor, 2),
    (ast.LShift, 1), (ast.RShift, 1),
]
_CMP_OPS = [
    (ast.Eq, 4), (ast.NotEq, 4), (ast.Lt, 3), (ast.Gt, 3),
    (ast.LtE, 2), (ast.GtE, 2), (ast.Is, 1), (ast.IsNot, 1),
    (ast.In, 2), (ast.NotIn, 2),
]
_BOOL_OPS = [(ast.And, 2), (ast.Or, 2)]
_UNARY_OPS = [(ast.UAdd, 1), (ast.USub, 2), (ast.Not, 2), (ast.Invert, 1)]

_LITERALS_INT = [0, 1, -1, 2, 7, 42, -100, 1000, 2 ** 31 - 1, 2 ** 63 - 1]
_LITERALS_FLOAT = [0.0, 1.0, -1.0, 3.14, 1e10, -1e10, 1e-10]
_LITERALS_STR = ["", "a", "abc", "hello"]
_LITERALS_BOOL = [True, False]
_LITERALS_NONE = [None]


def _weighted(pool):
    out = []
    for cls, w in pool:
        out.extend([cls] * w)
    return out


_BIN_OP_POOL = _weighted(_BIN_OPS)
_CMP_OP_POOL = _weighted(_CMP_OPS)
_BOOL_OP_POOL = _weighted(_BOOL_OPS)
_UNARY_OP_POOL = _weighted(_UNARY_OPS)


class ASTFuzzer:
    def __init__(self, rng: random.Random, *, max_depth: int = 6, max_nodes: int = 80) -> None:
        self.rng = rng
        self.max_depth = max_depth
        self.max_nodes = max_nodes
        self.node_count = 0

    def reset(self) -> None:
        self.node_count = 0

    def expr(self, depth: int = 0) -> ast.expr:
        if self.node_count >= self.max_nodes:
            return self._literal()
        if depth >= self.max_depth:
            return self._literal()
        self.node_count += 1

        choices = [
            ("literal", 5),
            ("name", 4),
            ("binop", 6),
            ("compare", 4),
            ("boolop", 3),
            ("unaryop", 3),
            ("ifexp", 2),
            ("call", 4),
            ("list", 2),
            ("dict", 1),
            ("subscript", 2),
        ]
        weights = [w for _, w in choices]
        names = [n for n, _ in choices]
        kind = self.rng.choices(names, weights=weights, k=1)[0]

        if kind == "literal":
            return self._literal()
        if kind == "name":
            return self._name()
        if kind == "binop":
            left = self.expr(depth + 1)
            right = self.expr(depth + 1)
            op = self.rng.choice(_BIN_OP_POOL)()
            return ast.BinOp(left=left, op=op, right=right)
        if kind == "compare":
            left = self.expr(depth + 1)
            n_cmps = self.rng.randint(1, 2)
            ops = [self.rng.choice(_CMP_OP_POOL)() for _ in range(n_cmps)]
            comparators = [self.expr(depth + 1) for _ in range(n_cmps)]
            return ast.Compare(left=left, ops=ops, comparators=comparators)
        if kind == "boolop":
            n = self.rng.randint(2, 3)
            op = self.rng.choice(_BOOL_OP_POOL)()
            values = [self.expr(depth + 1) for _ in range(n)]
            return ast.BoolOp(op=op, values=values)
        if kind == "unaryop":
            operand = self.expr(depth + 1)
            op = self.rng.choice(_UNARY_OP_POOL)()
            return ast.UnaryOp(op=op, operand=operand)
        if kind == "ifexp":
            test = self.expr(depth + 1)
            body = self.expr(depth + 1)
            orelse = self.expr(depth + 1)
            return ast.IfExp(test=test, body=body, orelse=orelse)
        if kind == "call":
            fn = self._name()
            args = [self.expr(depth + 1) for _ in range(self.rng.randint(0, 2))]
            return ast.Call(func=fn, args=args, keywords=[])
        if kind == "list":
            n = self.rng.randint(0, 3)
            elts = [self.expr(depth + 1) for _ in range(n)]
            return ast.List(elts=elts, ctx=ast.Load())
        if kind == "dict":
            n = self.rng.randint(0, 3)
            keys = [self.expr(depth + 1) for _ in range(n)]
            vals = [self.expr(depth + 1) for _ in range(n)]
            return ast.Dict(keys=keys, values=vals)
        if kind == "subscript":
            value = self._name()
            slice_val = self.expr(depth + 1)
            return ast.Subscript(value=value, slice=ast.Index(value=slice_val), ctx=ast.Load())
        return self._literal()

    def _literal(self) -> ast.expr:
        kind = self.rng.choices(
            ["int", "float", "str", "bool", "none", "list"],
            weights=[5, 3, 2, 2, 1, 1], k=1)[0]
        if kind == "int":
            return ast.Constant(self.rng.choice(_LITERALS_INT))
        if kind == "float":
            return ast.Constant(self.rng.choice(_LITERALS_FLOAT))
        if kind == "str":
            return ast.Constant(self.rng.choice(_LITERALS_STR))
        if kind == "bool":
            return ast.Constant(self.rng.choice(_LITERALS_BOOL))
        if kind == "none":
            return ast.Constant(None)
        return ast.List(elts=[], ctx=ast.Load())

    def _name(self) -> ast.Name:
        names = ["x", "y", "z", "a", "b", "len", "abs", "min", "max", "sum"]
        return ast.Name(id=self.rng.choice(names), ctx=ast.Load())

    def program(self) -> ast.Module:
        self.reset()
        # Build a function main() that does some computation and returns
        # an expression. Variables are bound to a few sensible defaults
        # so the program likely runs without NameError.
        body = []
        # Bind some names first
        for name, val in [
            ("x", ast.Constant(self.rng.choice(_LITERALS_INT))),
            ("y", ast.Constant(self.rng.choice(_LITERALS_INT))),
            ("z", ast.Constant(self.rng.choice(_LITERALS_INT))),
            ("a", ast.List(elts=[ast.Constant(i) for i in range(5)], ctx=ast.Load())),
            ("b", ast.List(elts=[ast.Constant(i) for i in range(5, 10)], ctx=ast.Load())),
        ]:
            body.append(ast.Assign(
                targets=[ast.Name(id=name, ctx=ast.Store())],
                value=val,
            ))
        # Then return an expression
        ret_expr = self.expr(depth=0)
        body.append(ast.Return(value=ret_expr))
        fn = ast.FunctionDef(
            name="main",
            args=ast.arguments(
                posonlyargs=[], args=[], vararg=None,
                kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[],
            ),
            body=body,
            decorator_list=[],
            returns=None,
        )
        return ast.Module(body=[fn], type_ignores=[])


def generate(*, n: int = 300_000, seed: int = 0) -> Iterator[TestCase]:
    rng = random.Random(seed)
    fuzzer = ASTFuzzer(rng)
    for i in range(n):
        mod = fuzzer.program()
        try:
            ast.fix_missing_locations(mod)
            source = ast.unparse(mod)
            # Sanity: must compile
            compile(source, "<fuzz>", "exec")
        except Exception:
            # Skip malformed programs (shouldn't happen but be defensive)
            continue
        # Pick opt state per case
        opt = rng.choices(
            [OptState.COLD, OptState.WARM, OptState.HOT],
            weights=[5, 3, 2], k=1)[0]
        yield TestCase(
            source=source,
            inputs=(),
            tags=TagSet.make(
                "language_semantics",
                type_stability="unknown",
                control_flow="straight_line",
                call_behavior="direct",
                opt_state=opt.value,
                tags={"fuzz", "ast", "generated"},
            ),
            id=f"fuzz-ast-{i:08d}",
            category="fuzz_ast",
        )
