"""Corpus loader: stream :class:`TestCase` objects from a JSONL file.

Each line of a corpus JSONL file is one test case::

    {"id": "num-0000001", "category": "numeric",
     "source": "def main():\\n    ...\\n",
     "inputs": {},
     "tags": {"semantic": "numeric", "type_stability": "monomorphic",
              "control_flow": "loop", "call_behavior": "direct",
              "opt_state": "cold", "tags": ["numeric", "add"]}}

This lets us materialize the 200K + 1M test suite once and then load
it for execution without re-running the generators (which is much
faster for fuzz engines that produce large numbers of cases).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterator

from .tags import TagSet
from .runner import TestCase
from .states import OptState


def case_to_json(case: TestCase) -> dict:
    """Serialize a TestCase to a JSON-friendly dict."""
    return {
        "id": case.id or case.stable_id(),
        "category": case.category,
        "source": case.source,
        "inputs": [[k, repr(v)] for k, v in case.inputs],  # repr for safety
        "tags": case.tags.as_dict(),
    }


def case_from_json(d: dict) -> TestCase:
    """Deserialize a TestCase from a JSON dict."""
    # Note: inputs are stored as repr strings; we don't auto-eval them
    # because that's a security hole. The harness re-binds inputs from
    # the source's own definitions where possible.
    inputs = tuple((k, v) for k, v in d.get("inputs", []))
    tags_dict = d.get("tags", {})
    tags = TagSet.make(
        semantic=tags_dict.get("semantic", "language_semantics"),
        type_stability=tags_dict.get("type_stability", "unknown"),
        control_flow=tags_dict.get("control_flow", "straight_line"),
        call_behavior=tags_dict.get("call_behavior", "direct"),
        opt_state=tags_dict.get("opt_state", "cold"),
        tags=tags_dict.get("tags", []),
    )
    return TestCase(
        source=d["source"],
        inputs=inputs,
        tags=tags,
        id=d.get("id"),
        category=d.get("category"),
    )


def write_jsonl(cases: Iterator[TestCase], path: str | os.PathLike[str]) -> int:
    """Write cases to a JSONL file. Returns number of cases written."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("w", encoding="utf-8") as f:
        for case in cases:
            f.write(json.dumps(case_to_json(case), default=str) + "\n")
            n += 1
    return n


def read_jsonl(path: str | os.PathLike[str]) -> Iterator[TestCase]:
    """Stream cases from a JSONL file. Transparently handles .gz."""
    p = Path(path)
    if p.suffix == ".gz":
        import gzip
        opener = gzip.open
    else:
        opener = open
    with opener(p, "rt", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield case_from_json(json.loads(line))


def read_all_jsonl(root: str | os.PathLike[str]) -> Iterator[TestCase]:
    """Stream cases from every .jsonl or .jsonl.gz file under ``root``
    (sorted by name)."""
    root = Path(root)
    if not root.exists():
        return
    files = []
    for path in root.rglob("*.jsonl"):
        files.append(path)
    for path in root.rglob("*.jsonl.gz"):
        files.append(path)
    for path in sorted(files):
        yield from read_jsonl(path)


__all__ = [
    "case_to_json",
    "case_from_json",
    "write_jsonl",
    "read_jsonl",
    "read_all_jsonl",
]
