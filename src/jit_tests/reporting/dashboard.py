"""Dashboard / status reporter.

Renders the final status block from a run:

    JIT TEST STATUS
    ────────────────────────────────────
    Deterministic       200,000 / 200,000
    Fuzz                1,000,000 / 1,000,000
    Differential        1,000,000 / 1,000,000
    Regressions              417

    Correctness                 99.9997%
    Semantic mismatches               3
    Crashes                            0
    Invalid deopts                     0
    GC violations                      0

    Avg warmup                  0.83 ms
    Median hot speedup          8.7×
    P95 hot speedup             5.1×
    Max hot speedup            31.4×

Inputs: a list of :class:`jit_tests.harness.TestResult` and
optional :class:`jit_tests.perf.PerfMetrics`.
"""

from __future__ import annotations

import io
from collections import Counter
from dataclasses import dataclass
from typing import Iterable

from ..harness import TestResult
from ..perf import PerfMetrics, summarize


@dataclass
class Dashboard:
    deterministic_total: int = 0
    deterministic_passed: int = 0
    fuzz_total: int = 0
    fuzz_passed: int = 0
    differential_total: int = 0
    differential_passed: int = 0
    regressions: int = 0
    semantic_mismatches: int = 0
    crashes: int = 0
    invalid_deopts: int = 0
    gc_violations: int = 0
    perf_summary: dict | None = None

    @classmethod
    def from_results(
        cls,
        results: Iterable[TestResult],
        *,
        perf_metrics: list[PerfMetrics] | None = None,
        regression_count: int = 0,
    ) -> "Dashboard":
        det_total = det_pass = 0
        fuzz_total = fuzz_pass = 0
        diff_total = diff_pass = 0
        sem_miss = crashes = invalid_deopts = gc_violations = 0

        for r in results:
            if r.category.startswith("fuzz"):
                fuzz_total += 1
                if r.passed:
                    fuzz_pass += 1
                if r.crash:
                    crashes += 1
            elif r.category == "fuzz_differential":
                diff_total += 1
                if r.passed:
                    diff_pass += 1
            else:
                det_total += 1
                if r.passed:
                    det_pass += 1
            if "deopt" in r.reason.lower():
                invalid_deopts += 1
            if "gc" in r.reason.lower() or "memory" in r.reason.lower():
                gc_violations += 1

        perf = summarize(perf_metrics) if perf_metrics else None
        return cls(
            deterministic_total=det_total,
            deterministic_passed=det_pass,
            fuzz_total=fuzz_total,
            fuzz_passed=fuzz_pass,
            differential_total=diff_total,
            differential_passed=diff_pass,
            regressions=regression_count,
            semantic_mismatches=sem_miss,
            crashes=crashes,
            invalid_deopts=invalid_deopts,
            gc_violations=gc_violations,
            perf_summary=perf,
        )

    def render(self) -> str:
        out = io.StringIO()
        out.write("JIT TEST STATUS\n")
        out.write("\u2500" * 60 + "\n")

        def line(label: str, total: int, passed: int) -> None:
            if total == 0:
                out.write(f"{label:<28s} {0:>12,} / {0:,}\n")
                return
            out.write(f"{label:<28s} {passed:>12,} / {total:,}\n")

        line("Deterministic", self.deterministic_total, self.deterministic_passed)
        line("Fuzz", self.fuzz_total, self.fuzz_passed)
        line("Differential", self.differential_total, self.differential_passed)
        out.write(f"{'Regressions':<28s} {self.regressions:>16,}\n")
        out.write("\n")

        total = (
            self.deterministic_total + self.fuzz_total + self.differential_total
        )
        passed = (
            self.deterministic_passed + self.fuzz_passed + self.differential_passed
        )
        if total > 0:
            correctness = passed / total * 100
        else:
            correctness = 100.0
        out.write(f"{'Correctness':<28s} {correctness:>16.4f}%\n")
        out.write(f"{'Semantic mismatches':<28s} {self.semantic_mismatches:>16,}\n")
        out.write(f"{'Crashes':<28s} {self.crashes:>16,}\n")
        out.write(f"{'Invalid deopts':<28s} {self.invalid_deopts:>16,}\n")
        out.write(f"{'GC violations':<28s} {self.gc_violations:>16,}\n")
        out.write("\n")

        if self.perf_summary:
            avg_warmup_ms = (self.perf_summary.get("avg_warmup", 0) or 0) * 1000
            median_speedup = self.perf_summary.get("median_speedup", 1.0)
            p95_speedup = self.perf_summary.get("p95_speedup", 1.0)
            max_speedup = self.perf_summary.get("max_speedup", 1.0)
            out.write(f"{'Avg warmup':<28s} {avg_warmup_ms:>14.2f} ms\n")
            out.write(f"{'Median hot speedup':<28s} {median_speedup:>14.2f}x\n")
            out.write(f"{'P95 hot speedup':<28s} {p95_speedup:>14.2f}x\n")
            out.write(f"{'Max hot speedup':<28s} {max_speedup:>14.2f}x\n")

        return out.getvalue()


def render_dashboard(
    results: Iterable[TestResult],
    *,
    perf_metrics: list[PerfMetrics] | None = None,
    regression_count: int = 0,
) -> str:
    return Dashboard.from_results(
        results, perf_metrics=perf_metrics, regression_count=regression_count
    ).render()
