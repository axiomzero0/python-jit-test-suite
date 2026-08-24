"""ML / scientific kernels: 10K tests.

Axes:

    kernel          : elementwise | dot | reduction | matvec | matmul |
                      stencil | softmax | normalize | activation |
                      broadcast
    dtype           : float | int | mixed
    size           : 8 | 32 | 128 | 1024
    opt_state      : all 6
"""

from __future__ import annotations

from typing import Iterator

from ..harness import OptState, TagSet, TestCase
from ._common import GridBuilder, param_grid


KERNELS = (
    "elementwise", "dot", "reduction", "matvec", "matmul",
    "stencil", "softmax", "normalize", "activation", "broadcast",
)
DTYPES = ("float", "int", "mixed")
SIZES = (8, 32, 128, 1024)
OPT_STATES = [OptState.COLD, OptState.WARM, OptState.HOT, OptState.VERY_HOT, OptState.DEOPT, OptState.REHEATED]


def _kernel_source(kernel: str, dtype: str, size: int) -> str:
    if dtype == "float":
        suffix = "0.0"
        init = "float(i)"
    elif dtype == "int":
        suffix = "0"
        init = "i"
    else:
        suffix = "0.0"
        init = "i + 0.5"

    if kernel == "elementwise":
        return (
            f"def main():\n"
            f"    a = [{init} for i in range({size})]\n"
            f"    b = [{init} for i in range({size})]\n"
            f"    out = [a[i] * b[i] + 1.0 for i in range({size})]\n"
            f"    return out[-1]\n"
        )
    if kernel == "dot":
        return (
            f"def main():\n"
            f"    a = [{init} for i in range({size})]\n"
            f"    b = [{init} for i in range({size})]\n"
            f"    s = {suffix}\n"
            f"    for i in range({size}):\n"
            f"        s += a[i] * b[i]\n"
            f"    return s\n"
        )
    if kernel == "reduction":
        return (
            f"def main():\n"
            f"    a = [{init} for i in range({size})]\n"
            f"    s = {suffix}\n"
            f"    for v in a:\n"
            f"        s += v\n"
            f"    return s\n"
        )
    if kernel == "matvec":
        # size x size matrix, size-vector; loop nest
        return (
            f"def main():\n"
            f"    N = {size}\n"
            f"    M = [[float(i * N + j) for j in range(N)] for i in range(N)]\n"
            f"    v = [float(i) for i in range(N)]\n"
            f"    out = [0.0] * N\n"
            f"    for i in range(N):\n"
            f"        s = 0.0\n"
            f"        for j in range(N):\n"
            f"            s += M[i][j] * v[j]\n"
            f"        out[i] = s\n"
            f"    return out[N // 2]\n"
        )
    if kernel == "matmul":
        # Use smaller size for matmul (O(n^3))
        s = min(size, 32)
        return (
            f"def main():\n"
            f"    N = {s}\n"
            f"    A = [[float(i * N + j) for j in range(N)] for i in range(N)]\n"
            f"    B = [[float(j * N + k) for k in range(N)] for j in range(N)]\n"
            f"    C = [[0.0] * N for _ in range(N)]\n"
            f"    for i in range(N):\n"
            f"        for j in range(N):\n"
            f"            s = 0.0\n"
            f"            for k in range(N):\n"
            f"                s += A[i][k] * B[k][j]\n"
            f"            C[i][j] = s\n"
            f"    return C[N // 2][N // 2]\n"
        )
    if kernel == "stencil":
        return (
            f"def main():\n"
            f"    N = {size}\n"
            f"    a = [float(i) for i in range(N)]\n"
            f"    out = [0.0] * N\n"
            f"    for i in range(1, N - 1):\n"
            f"        out[i] = 0.25 * (a[i-1] + 2 * a[i] + a[i+1])\n"
            f"    return out[N // 2]\n"
        )
    if kernel == "softmax":
        return (
            f"import math\n"
            f"def main():\n"
            f"    N = {size}\n"
            f"    a = [float(i - N // 2) for i in range(N)]\n"
            f"    m = max(a)\n"
            f"    exps = [math.exp(v - m) for v in a]\n"
            f"    s = sum(exps)\n"
            f"    return sum(e / s for e in exps)\n"
        )
    if kernel == "normalize":
        return (
            f"import math\n"
            f"def main():\n"
            f"    N = {size}\n"
            f"    a = [float(i) for i in range(N)]\n"
            f"    mean = sum(a) / N\n"
            f"    var = sum((v - mean) ** 2 for v in a) / N\n"
            f"    std = math.sqrt(var)\n"
            f"    return [(v - mean) / std if std > 0 else 0.0 for v in a][-1]\n"
        )
    if kernel == "activation":
        return (
            f"def main():\n"
            f"    N = {size}\n"
            f"    a = [float(i - N // 2) for i in range(N)]\n"
            f"    relu = [v if v > 0 else 0.0 for v in a]\n"
            f"    return sum(relu)\n"
        )
    if kernel == "broadcast":
        return (
            f"def main():\n"
            f"    N = {size}\n"
            f"    a = [float(i) for i in range(N)]\n"
            f"    scalar = 3.14\n"
            f"    return sum(v * scalar + 1.0 for v in a)\n"
        )
    return "pass\n"


def _opt_for_size(size: int) -> OptState:
    if size <= 8:
        return OptState.COLD
    if size <= 32:
        return OptState.WARM
    if size <= 128:
        return OptState.HOT
    return OptState.VERY_HOT


def generate(*, n: int = 10_000, seed: int = 0) -> Iterator[TestCase]:
    gb = GridBuilder(category="ml_kernels", id_prefix="ml")
    grid = param_grid(kernel=KERNELS, dtype=DTYPES, size=SIZES, opt=OPT_STATES)

    materialized = list(gb.expand_simple(
        grid,
        lambda p: _kernel_source(p["kernel"], p["dtype"], p["size"]),
        tags_fn=lambda p: TagSet.make(
            "ml_kernels",
            type_stability="monomorphic",
            control_flow="nested_loop" if p["kernel"] in ("matmul", "matvec", "stencil") else "loop",
            call_behavior="direct",
            opt_state=p["opt"].value,
            tags={"ml", p["kernel"], p["dtype"], f"size_{p['size']}", "vectorization", "reduction"},
        ),
    ))

    for i in range(n):
        case = materialized[i % len(materialized)]
        yield TestCase(
            source=case.source,
            inputs=case.inputs,
            tags=case.tags,
            id=f"ml-{i:07d}",
            category=case.category,
        )
