"""Performance metrics collection.

For each hot workload we collect:

    interpreter_time
    baseline_jit_time
    optimized_jit_time
    cpython_time
    compile_time
    warmup_time
    peak_memory
    allocation_count
    deopt_count
    osr_count
    ic_miss_count
    guard_failures
    gc_time

And derive:

    speedup_vs_cpython
    speedup_vs_interpreter
    jit_compilation_overhead
    steady_state_throughput
    time_to_first_result

Each metric is captured by a :class:`MetricCollector` that the user can
subclass per JIT implementation. The default collector only knows how
to time things via :mod:`time` and measure RSS via :mod:`resource` /
:mod:`psutil` (optional).
"""

from __future__ import annotations

import gc
import statistics
import sys
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Iterator

try:
    import psutil  # type: ignore
    _HAS_PSUTIL = True
except ImportError:
    _HAS_PSUTIL = False

try:
    import resource
    _HAS_RESOURCE = True
except ImportError:
    _HAS_RESOURCE = False  # windows


@dataclass
class PerfMetrics:
    case_id: str
    category: str
    opt_state: str

    interpreter_time: float = 0.0
    baseline_jit_time: float = 0.0
    optimized_jit_time: float = 0.0
    cpython_time: float = 0.0
    compile_time: float = 0.0
    warmup_time: float = 0.0
    peak_memory_bytes: int = 0
    allocation_count: int = 0
    deopt_count: int = 0
    osr_count: int = 0
    ic_miss_count: int = 0
    guard_failures: int = 0
    gc_time: float = 0.0
    iterations: int = 1

    @property
    def speedup_vs_cpython(self) -> float:
        if self.optimized_jit_time <= 0:
            return 1.0
        return self.cpython_time / self.optimized_jit_time

    @property
    def speedup_vs_interpreter(self) -> float:
        if self.optimized_jit_time <= 0:
            return 1.0
        return self.interpreter_time / self.optimized_jit_time

    @property
    def jit_compilation_overhead(self) -> float:
        if self.optimized_jit_time <= 0:
            return 0.0
        return self.compile_time / (self.compile_time + self.optimized_jit_time)

    @property
    def steady_state_throughput(self) -> float:
        if self.optimized_jit_time <= 0:
            return 0.0
        return self.iterations / self.optimized_jit_time

    @property
    def time_to_first_result(self) -> float:
        return self.compile_time + self.warmup_time

    def as_dict(self) -> dict[str, Any]:
        d = self.__dict__.copy()
        d["speedup_vs_cpython"] = self.speedup_vs_cpython
        d["speedup_vs_interpreter"] = self.speedup_vs_interpreter
        d["jit_compilation_overhead"] = self.jit_compilation_overhead
        d["steady_state_throughput"] = self.steady_state_throughput
        d["time_to_first_result"] = self.time_to_first_result
        return d


def _peak_rss() -> int:
    if _HAS_PSUTIL:
        return psutil.Process().memory_info().peak_rss  # type: ignore
    if _HAS_RESOURCE:
        # ru_maxrss is in KB on Linux, bytes on macOS
        import resource as _r
        rss = _r.getrusage(_r.RUSAGE_SELF).ru_maxrss
        if sys.platform == "darwin":
            return rss * 1024
        return rss * 1024
    return 0


class MetricCollector:
    """Default collector. Only times CPython runs; subclass to plug in a JIT."""

    def __init__(self) -> None:
        self.deopt_count = 0
        self.osr_count = 0
        self.ic_miss_count = 0
        self.guard_failures = 0
        self.allocation_count = 0

    def reset(self) -> None:
        self.__init__()

    @contextmanager
    def measure(self) -> Iterator[dict[str, Any]]:
        gc.collect()
        gc.disable()
        t0 = time.perf_counter()
        try:
            yield {}
        finally:
            t1 = time.perf_counter()
            gc.enable()
            return_dict = {
                "wall_time": t1 - t0,
                "peak_rss": _peak_rss(),
            }
            self._last = return_dict  # type: ignore

    def collect(
        self,
        case,
        *,
        interpreter_fn=None,
        baseline_jit_fn=None,
        optimized_jit_fn=None,
        cpython_fn=None,
        iterations: int = 1,
    ) -> PerfMetrics:
        """Time the various execution paths for ``case`` and return metrics.

        Each ``fn`` is a callable that takes (source, inputs_dict) and
        returns the result of running the program once.
        """
        m = PerfMetrics(
            case_id=case.stable_id(),
            category=case.category or "unknown",
            opt_state=case.tags.opt_state.value,
            iterations=iterations,
        )

        # Always measure CPython (the reference) if cpython_fn is given
        if cpython_fn is None:
            from ..harness.oracle import run_cpython

            def cpython_fn(src, inputs):
                return run_cpython(src, inputs=inputs)

        # Warmup / compile time
        if baseline_jit_fn is not None:
            t0 = time.perf_counter()
            baseline_jit_fn(case.source, case.inputs_dict)  # warmup
            m.warmup_time = time.perf_counter() - t0

        if optimized_jit_fn is not None:
            t0 = time.perf_counter()
            for _ in range(iterations):
                optimized_jit_fn(case.source, case.inputs_dict)
            m.optimized_jit_time = time.perf_counter() - t0

        if baseline_jit_fn is not None:
            t0 = time.perf_counter()
            for _ in range(iterations):
                baseline_jit_fn(case.source, case.inputs_dict)
            m.baseline_jit_time = time.perf_counter() - t0

        if cpython_fn is not None:
            t0 = time.perf_counter()
            for _ in range(iterations):
                cpython_fn(case.source, case.inputs_dict)
            m.cpython_time = time.perf_counter() - t0

        m.peak_memory_bytes = _peak_rss()
        m.deopt_count = self.deopt_count
        m.osr_count = self.osr_count
        m.ic_miss_count = self.ic_miss_count
        m.guard_failures = self.guard_failures
        m.allocation_count = self.allocation_count
        return m


def summarize(metrics: list[PerfMetrics]) -> dict[str, Any]:
    """Aggregate a list of metrics into the dashboard's headline numbers."""
    if not metrics:
        return {}

    speedups = [m.speedup_vs_cpython for m in metrics if m.cpython_time > 0 and m.optimized_jit_time > 0]
    warmups = [m.warmup_time for m in metrics if m.warmup_time > 0]

    def _p(values: list[float], p: float) -> float:
        if not values:
            return 0.0
        s = sorted(values)
        idx = min(len(s) - 1, max(0, int(len(s) * p)))
        return s[idx]

    return {
        "n_workloads": len(metrics),
        "avg_warmup": statistics.mean(warmups) if warmups else 0.0,
        "median_speedup": statistics.median(speedups) if speedups else 1.0,
        "p95_speedup": _p(speedups, 0.95) if speedups else 1.0,
        "max_speedup": max(speedups) if speedups else 1.0,
        "min_speedup": min(speedups) if speedups else 1.0,
        "total_deopts": sum(m.deopt_count for m in metrics),
        "total_osrs": sum(m.osr_count for m in metrics),
        "total_ic_misses": sum(m.ic_miss_count for m in metrics),
        "total_guard_failures": sum(m.guard_failures for m in metrics),
    }
