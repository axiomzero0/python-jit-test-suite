"""Regression store: persist minimized failing fuzz cases as permanent
regression tests.

Layout:

    fuzz_failures/
        000001.py
        000001.meta.json
        000002.py
        000002.meta.json
        ...

Each ``.py`` file is the minimized failing source. Each ``.meta.json``
contains the test id, original fuzz case id, opt state, the failing
observation, and the bug description.

The store is append-only. New failures are added at the end.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path

from ..harness import TestCase
from ..harness.oracle import Observation


@dataclass
class RegressionEntry:
    index: int
    fuzz_id: str
    category: str
    opt_state: str
    original_source: str
    minimized_source: str
    expected_observation: dict
    actual_observation: dict
    reason: str
    bug_description: str = ""


class RegressionStore:
    def __init__(self, root: str | os.PathLike[str]) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _next_index(self) -> int:
        existing = sorted(self.root.glob("*.py"))
        if not existing:
            return 1
        last = existing[-1].stem
        try:
            return int(last) + 1
        except ValueError:
            return len(existing) + 1

    def add(
        self,
        *,
        fuzz_id: str,
        category: str,
        opt_state: str,
        original_source: str,
        minimized_source: str,
        expected: Observation,
        actual: Observation,
        reason: str,
        bug_description: str = "",
    ) -> int:
        idx = self._next_index()
        stem = f"{idx:06d}"
        src_path = self.root / f"{stem}.py"
        meta_path = self.root / f"{stem}.meta.json"

        src_path.write_text(minimized_source, encoding="utf-8")
        meta_path.write_text(
            json.dumps(
                RegressionEntry(
                    index=idx,
                    fuzz_id=fuzz_id,
                    category=category,
                    opt_state=opt_state,
                    original_source=original_source,
                    minimized_source=minimized_source,
                    expected_observation=expected.canonical(),
                    actual_observation=actual.canonical(),
                    reason=reason,
                    bug_description=bug_description,
                ).__dict__,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )
        return idx

    def __iter__(self):
        for meta in sorted(self.root.glob("*.meta.json")):
            data = json.loads(meta.read_text(encoding="utf-8"))
            yield RegressionEntry(**data)

    def __len__(self) -> int:
        return sum(1 for _ in self.root.glob("*.meta.json"))


def load_all(root: str | os.PathLike[str]) -> list[RegressionEntry]:
    store = RegressionStore(root)
    return list(store)
