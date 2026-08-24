"""Generate a manifest.json summarizing the materialized corpus."""

from __future__ import annotations

import gzip
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


def count_lines(path: Path) -> int:
    """Count JSONL lines, handling .gz transparently."""
    if path.suffix == ".gz":
        opener = gzip.open
    else:
        opener = open
    n = 0
    with opener(path, "rt", encoding="utf-8") as f:
        for _ in f:
            n += 1
    return n


def main() -> int:
    corpus = ROOT / "corpus"
    samples = ROOT / "samples"

    manifest = {
        "version": "1.0",
        "total_cases": 0,
        "deterministic": {"total": 0, "files": []},
        "fuzz": {"total": 0, "files": []},
        "samples": {"total": 0, "per_category": 50},
    }

    for kind in ("deterministic", "fuzz"):
        kind_dir = corpus / kind
        if not kind_dir.exists():
            continue
        for path in sorted(kind_dir.glob("*.jsonl*")):
            n = count_lines(path)
            size = path.stat().st_size
            manifest[kind]["files"].append({
                "name": path.stem if path.suffix == ".gz" else path.name,
                "path": str(path.relative_to(ROOT)),
                "cases": n,
                "bytes": size,
            })
            manifest[kind]["total"] += n
            manifest["total_cases"] += n

    # samples count
    sample_total = sum(1 for _ in samples.rglob("*.py")) if samples.exists() else 0
    manifest["samples"]["total"] = sample_total

    out = ROOT / "corpus" / "manifest.json"
    out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote {out.relative_to(ROOT)}")
    print(json.dumps({
        "total_cases": manifest["total_cases"],
        "deterministic_total": manifest["deterministic"]["total"],
        "fuzz_total": manifest["fuzz"]["total"],
        "samples_total": manifest["samples"]["total"],
        "files": len(manifest["deterministic"]["files"]) + len(manifest["fuzz"]["files"]),
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
