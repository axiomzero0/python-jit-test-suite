"""Materialize a test category or fuzz engine into a JSONL file.

Usage::

    python scripts/materialize.py deterministic numeric
    python scripts/materialize.py deterministic language_semantics
    python scripts/materialize.py fuzz ast
    python scripts/materialize.py fuzz mutation

Writes to::

    corpus/deterministic/<category>.jsonl
    corpus/fuzz/<engine>.jsonl
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

# Make the package importable when run from the repo root
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from jit_tests.harness import write_jsonl
from jit_tests.deterministic import generate_category, DEFAULT_COUNTS as DET_COUNTS
from jit_tests.fuzz import generate_engine, DEFAULT_COUNTS as FUZZ_COUNTS


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(__doc__)
        return 1
    kind = argv[1]
    name = argv[2]
    override_n = int(argv[3]) if len(argv) >= 4 else None

    if kind == "deterministic":
        if name not in DET_COUNTS:
            print(f"unknown deterministic category: {name}")
            return 1
        n = override_n if override_n is not None else DET_COUNTS[name]
        out = ROOT / "corpus" / "deterministic" / f"{name}.jsonl"
        out.parent.mkdir(parents=True, exist_ok=True)
        print(f"Materializing {n:,} {name} cases -> {out.relative_to(ROOT)}", flush=True)
        t0 = time.perf_counter()
        written = write_jsonl(generate_category(name, n=n, seed=0xC0FFEE), out)
        dt = time.perf_counter() - t0
        size_kb = out.stat().st_size // 1024
        print(f"  Wrote {written:,} cases in {dt:.1f}s ({size_kb:,} KB)", flush=True)
        return 0

    if kind == "fuzz":
        if name not in FUZZ_COUNTS:
            print(f"unknown fuzz engine: {name}")
            return 1
        n = override_n if override_n is not None else FUZZ_COUNTS[name]
        out = ROOT / "corpus" / "fuzz" / f"{name}.jsonl"
        out.parent.mkdir(parents=True, exist_ok=True)
        print(f"Materializing {n:,} {name} fuzz cases -> {out.relative_to(ROOT)}", flush=True)
        t0 = time.perf_counter()
        written = write_jsonl(generate_engine(name, n=n, seed=0xF123), out)
        dt = time.perf_counter() - t0
        size_kb = out.stat().st_size // 1024
        print(f"  Wrote {written:,} cases in {dt:.1f}s ({size_kb:,} KB)", flush=True)
        return 0

    print(f"unknown kind: {kind}; expected 'deterministic' or 'fuzz'")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
