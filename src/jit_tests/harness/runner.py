"""Core test case + runner.

A :class:`TestCase` is the atomic unit of the suite. Each case is:

    source      - Python source string
    inputs      - dict of globals to inject before exec
    expected    - optional precomputed expected observation (skips reference run)
    tags        - TagSet describing what this test exercises
    id          - stable string id (used as filename in regression reports)
    category    - top-level category name (matches TagSet.semantic by default)

The :class:`Runner` executes each case under a :class:`StateController`
(usually a CPython reference controller and a JIT candidate controller),
then compares results via :func:`jit_tests.harness.oracle.compare`.

Runners are stateless: the same case fed to the same runner with the same
controllers always produces the same result. This is what lets us parallelize
the 200K + 1M matrix across processes/cores.
"""

from __future__ import annotations

import hashlib
import time
import traceback
from dataclasses import dataclass, field
from typing import Iterable, Iterator

from .oracle import Observation, compare, run_cpython
from .states import StateController
from .tags import OptState, TagSet


@dataclass(frozen=True)
class TestCase:
    source: str
    inputs: tuple[tuple[str, object], ...] = ()
    expected: Observation | None = None
    tags: TagSet = field(default_factory=TagSet)
    id: str | None = None
    category: str | None = None

    @property
    def inputs_dict(self) -> dict[str, object]:
        return dict(self.inputs)

    def stable_id(self) -> str:
        if self.id is not None:
            return self.id
        h = hashlib.sha1()
        h.update(self.source.encode("utf-8"))
        for k, v in self.inputs:
            h.update(b"\x00")
            h.update(repr(v).encode("utf-8"))
        h.update(str(self.tags).encode("utf-8"))
        return h.hexdigest()[:16]

    def with_opt_state(self, state: OptState | str) -> "TestCase":
        return TestCase(
            source=self.source,
            inputs=self.inputs,
            expected=self.expected,
            tags=TagSet(
                semantic=self.tags.semantic,
                type_stability=self.tags.type_stability,
                control_flow=self.tags.control_flow,
                call_behavior=self.tags.call_behavior,
                opt_state=OptState(state) if isinstance(state, str) else state,
                tags=self.tags.tags,
            ),
            id=self.id,
            category=self.category,
        )


@dataclass
class TestResult:
    case_id: str
    category: str
    opt_state: str
    passed: bool
    reason: str = "ok"
    duration_ref: float = 0.0
    duration_cand: float = 0.0
    crash: bool = False
    crash_tb: str | None = None

    def as_dict(self) -> dict:
        return {
            "case_id": self.case_id,
            "category": self.category,
            "opt_state": self.opt_state,
            "passed": self.passed,
            "reason": self.reason,
            "duration_ref": self.duration_ref,
            "duration_cand": self.duration_cand,
            "crash": self.crash,
            "crash_tb": self.crash_tb,
        }


@dataclass
class Runner:
    reference: StateController = field(default_factory=StateController)
    candidate: StateController = field(default_factory=StateController)
    capture_globals: tuple[str, ...] = ()

    def run_one(
        self,
        case: TestCase,
        *,
        opt_state: OptState | str | None = None,
    ) -> TestResult:
        state = (
            opt_state
            if opt_state is not None
            else case.tags.opt_state
        )
        case_for_state = case if opt_state is None else case.with_opt_state(state)

        t0 = time.perf_counter()
        try:
            ref_obs = self.reference.run(
                case_for_state.source,
                inputs=case_for_state.inputs_dict,
                opt_state=state,
                capture_globals=self.capture_globals,
            )
        except BaseException as e:  # noqa: BLE001 - reference crash = test bug
            return TestResult(
                case_id=case_for_state.stable_id(),
                category=case_for_state.category or case_for_state.tags.semantic.value,
                opt_state=OptState(state).value if isinstance(state, str) else state.value,
                passed=False,
                reason=f"reference harness crashed: {e!r}",
                duration_ref=time.perf_counter() - t0,
                crash=True,
                crash_tb=traceback.format_exc(),
            )
        t_ref = time.perf_counter() - t0

        t1 = time.perf_counter()
        try:
            cand_obs = self.candidate.run(
                case_for_state.source,
                inputs=case_for_state.inputs_dict,
                opt_state=state,
                capture_globals=self.capture_globals,
            )
        except BaseException as e:  # noqa: BLE001 - candidate crash is interesting
            return TestResult(
                case_id=case_for_state.stable_id(),
                category=case_for_state.category or case_for_state.tags.semantic.value,
                opt_state=OptState(state).value if isinstance(state, str) else state.value,
                passed=False,
                reason=f"candidate harness crashed: {e!r}",
                duration_ref=t_ref,
                duration_cand=time.perf_counter() - t1,
                crash=True,
                crash_tb=traceback.format_exc(),
            )
        t_cand = time.perf_counter() - t1

        ok, reason = compare(ref_obs, cand_obs)
        return TestResult(
            case_id=case_for_state.stable_id(),
            category=case_for_state.category or case_for_state.tags.semantic.value,
            opt_state=OptState(state).value if isinstance(state, str) else state.value,
            passed=ok,
            reason=reason,
            duration_ref=t_ref,
            duration_cand=t_cand,
        )

    def run_many(
        self,
        cases: Iterable[TestCase],
        *,
        opt_states: Iterable[OptState | str] | None = None,
    ) -> Iterator[TestResult]:
        """Run each case across all requested opt states."""
        states = list(opt_states) if opt_states is not None else [None]
        for case in cases:
            for state in states:
                yield self.run_one(case, opt_state=state)
