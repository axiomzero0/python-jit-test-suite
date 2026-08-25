"""Generate reviewable individual .py test files for browsing.

Each category gets N sample test cases written as standalone .py files
under samples/<kind>/<category>/NNNNNN.py so users can browse them
without unzipping the corpus.

The samples are pure-source: they include a header comment with the
test id and tags, followed by the test source itself.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from jit_tests.deterministic import generate_category, DEFAULT_COUNTS as DET_COUNTS
from jit_tests.fuzz import generate_engine, DEFAULT_COUNTS as FUZZ_COUNTS


def emit_sample(case, out_path: Path) -> None:
    """Write a single case as a standalone .py file."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tags = case.tags
    header = [
        "# -*- coding: utf-8 -*-",
        f"# test_id: {case.id}",
        f"# category: {case.category}",
        f"# semantic: {tags.semantic.value}",
        f"# type_stability: {tags.type_stability.value}",
        f"# control_flow: {tags.control_flow.value}",
        f"# call_behavior: {tags.call_behavior.value}",
        f"# opt_state: {tags.opt_state.value}",
        f"# tags: {sorted(tags.tags)}",
        "",
    ]
    out_path.write_text("\n".join(header) + case.source + "\n", encoding="utf-8")


def main() -> int:
    n_per = 50
    samples_root = ROOT / "samples"
    if samples_root.exists():
        import shutil
        shutil.rmtree(samples_root)

    total = 0
    for cat in DET_COUNTS:
        out_dir = samples_root / "deterministic" / cat
        for i, case in enumerate(generate_category(cat, n=n_per, seed=0xC0FFEE)):
            emit_sample(case, out_dir / f"{i:04d}.py")
            total += 1
        print(f"  deterministic/{cat}: {n_per} samples")

    for eng in FUZZ_COUNTS:
        out_dir = samples_root / "fuzz" / eng
        for i, case in enumerate(generate_engine(eng, n=n_per, seed=0xF123)):
            emit_sample(case, out_dir / f"{i:04d}.py")
            total += 1
        print(f"  fuzz/{eng}: {n_per} samples")

    print(f"\nTotal samples: {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
