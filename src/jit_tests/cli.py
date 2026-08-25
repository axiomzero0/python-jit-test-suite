"""Command-line entry point.

Usage::

    jit-suite deterministic --limit 1000 --opt-state cold
    jit-suite fuzz --engine ast --limit 1000
    jit-suite fuzz --engine differential --limit 1000 --minimize
    jit-suite all --limit 100
    jit-suite dashboard --from results.jsonl
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable

from .harness import Runner, StateController, TestResult
from .deterministic import DEFAULT_COUNTS as DET_COUNTS
from .deterministic import generate_all as gen_all_det
from .deterministic import generate_category as gen_cat_det
from .fuzz import DEFAULT_COUNTS as FUZZ_COUNTS
from .fuzz import generate_all as gen_all_fuzz
from .fuzz import generate_engine as gen_engine_fuzz
from .fuzz.regressions import RegressionStore
from .reporting import render_dashboard


def _runner() -> Runner:
    """Default runner: CPython reference + CPython candidate (trivial baseline).

    Plug in a real JIT by subclassing :class:`StateController` and passing
    it as the candidate.
    """
    return Runner(reference=StateController(), candidate=StateController())


def _write_jsonl(results: Iterable[TestResult], path: Path) -> int:
    n = 0
    with path.open("w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r.as_dict(), default=str) + "\n")
            n += 1
    return n


def cmd_deterministic(args: argparse.Namespace) -> int:
    runner = _runner()
    if args.category:
        cases = gen_cat_det(args.category, n=args.limit or DET_COUNTS[args.category], seed=args.seed)
    else:
        cases = gen_all_det(seed=args.seed)
        if args.limit:
            cases = list(cases)[: args.limit]

    results = []
    for i, case in enumerate(cases):
        if args.limit and i >= args.limit:
            break
        r = runner.run_one(case, opt_state=args.opt_state) if args.opt_state else runner.run_one(case)
        results.append(r)
        if not r.passed and args.verbose:
            print(f"FAIL {case.id}: {r.reason[:200]}", file=sys.stderr)

    if args.output:
        n = _write_jsonl(results, Path(args.output))
        print(f"Wrote {n} results to {args.output}")
    print(render_dashboard(results))
    return 0


def cmd_fuzz(args: argparse.Namespace) -> int:
    runner = _runner()
    store = RegressionStore(args.regression_dir) if args.minimize else None

    if args.engine:
        cases = gen_engine_fuzz(args.engine, n=args.limit or FUZZ_COUNTS[args.engine], seed=args.seed)
    else:
        cases = gen_all_fuzz(seed=args.seed)
        if args.limit:
            cases = list(cases)[: args.limit]

    results = []
    for i, case in enumerate(cases):
        if args.limit and i >= args.limit:
            break
        r = runner.run_one(case)
        results.append(r)
        if not r.passed:
            if args.verbose:
                print(f"FAIL {case.id}: {r.reason[:200]}", file=sys.stderr)
            if store is not None:
                from .harness.oracle import run_cpython
                # Minimize and store as a regression
                from .fuzz.minimizer import minimize
                expected = run_cpython(case.source, inputs=case.inputs_dict)
                report = minimize(case, expected=expected)
                store.add(
                    fuzz_id=case.id,
                    category=case.category,
                    opt_state=case.tags.opt_state.value,
                    original_source=case.source,
                    minimized_source=report.minimized_source,
                    expected=expected,
                    actual=expected,  # placeholder; real impl would capture JIT output
                    reason=r.reason,
                )

    if args.output:
        n = _write_jsonl(results, Path(args.output))
        print(f"Wrote {n} results to {args.output}")
    print(render_dashboard(results, regression_count=len(store) if store else 0))
    return 0


def cmd_all(args: argparse.Namespace) -> int:
    runner = _runner()
    results = []
    for i, case in enumerate(gen_all_det(seed=args.seed)):
        if args.limit and i >= args.limit:
            break
        results.append(runner.run_one(case))
    for i, case in enumerate(gen_all_fuzz(seed=args.seed)):
        if args.limit and i >= args.limit:
            break
        results.append(runner.run_one(case))

    if args.output:
        n = _write_jsonl(results, Path(args.output))
        print(f"Wrote {n} results to {args.output}")
    print(render_dashboard(results))
    return 0


def cmd_dashboard(args: argparse.Namespace) -> int:
    results = []
    for line in Path(args.from_file).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        d = json.loads(line)
        results.append(TestResult(**{k: d[k] for k in (
            "case_id", "category", "opt_state", "passed", "reason",
            "duration_ref", "duration_cand", "crash", "crash_tb"
        ) if k in d}))
    print(render_dashboard(results))
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="jit-suite", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    p_det = sub.add_parser("deterministic", help="Run the 200K deterministic suite")
    p_det.add_argument("--category", choices=list(DET_COUNTS))
    p_det.add_argument("--limit", type=int, default=None)
    p_det.add_argument("--opt-state", default=None)
    p_det.add_argument("--seed", type=int, default=0xC0FFEE)
    p_det.add_argument("--output", default=None, help="Write JSONL results to this path")
    p_det.add_argument("--verbose", action="store_true")
    p_det.set_defaults(func=cmd_deterministic)

    p_fuzz = sub.add_parser("fuzz", help="Run a fuzzing engine")
    p_fuzz.add_argument("--engine", choices=list(FUZZ_COUNTS))
    p_fuzz.add_argument("--limit", type=int, default=None)
    p_fuzz.add_argument("--seed", type=int, default=0xFUZZ if False else 0xF1234)
    p_fuzz.add_argument("--output", default=None)
    p_fuzz.add_argument("--verbose", action="store_true")
    p_fuzz.add_argument("--minimize", action="store_true", help="Minimize and store failing cases as regressions")
    p_fuzz.add_argument("--regression-dir", default="fuzz_failures")
    p_fuzz.set_defaults(func=cmd_fuzz)

    p_all = sub.add_parser("all", help="Run deterministic + fuzz")
    p_all.add_argument("--limit", type=int, default=None)
    p_all.add_argument("--seed", type=int, default=0xC0FFEE)
    p_all.add_argument("--output", default=None)
    p_all.set_defaults(func=cmd_all)

    p_dash = sub.add_parser("dashboard", help="Render dashboard from JSONL")
    p_dash.add_argument("--from-file", required=True)
    p_dash.set_defaults(func=cmd_dashboard)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
