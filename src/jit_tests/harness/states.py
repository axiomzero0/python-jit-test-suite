"""JIT state control: warmup, forced deopt, IC invalidation, OSR triggers.

Each JIT exposes its own knobs, but the harness uses a uniform abstraction:

    StateController.run(program, *, opt_state)

where ``opt_state`` is one of:

    cold        - single execution, no warmup
    warm        - small warmup loop, then collect
    hot         - large warmup loop, then collect
    very_hot    - very large warmup, expect full optimization
    deoptimized - run hot, then trigger deopt, then collect
    reheated    - deopt then re-warm

A real JIT will subclass :class:`StateController` to override
:meth:`warmup`, :meth:`force_deopt`, :meth:`invalidate_ic`, :meth:`trigger_gc`.

The default controller only knows how to run under CPython and behaves as
a no-op for state manipulation (since CPython has no JIT). It is still
useful for differential fuzzing where CPython is the reference.
"""

from __future__ import annotations

import gc
from dataclasses import dataclass
from enum import Enum

from .oracle import Observation, run_cpython
from .tags import OptState


class StateController:
    """Abstract controller. Subclass per JIT."""

    def warmup(self, source: str, inputs: dict, n: int) -> None:
        """Run ``source`` ``n`` times to warm up the JIT."""
        for _ in range(n):
            try:
                run_cpython(source, inputs=inputs)
            except Exception:  # noqa: BLE001
                pass

    def force_deopt(self, source: str, inputs: dict) -> None:
        """Trigger deoptimization of any compiled frame for ``source``."""
        # No-op for CPython
        return

    def invalidate_ic(self, source: str, inputs: dict) -> None:
        """Invalidate inline caches for the source."""
        return

    def trigger_gc(self) -> None:
        gc.collect()

    def run(
        self,
        source: str,
        *,
        inputs: dict | None = None,
        opt_state: OptState | str = OptState.COLD,
        capture_globals: tuple[str, ...] = (),
        timeout: float | None = None,
    ) -> Observation:
        state = OptState(opt_state) if isinstance(opt_state, str) else opt_state
        inputs = dict(inputs or {})

        if state is OptState.COLD:
            return run_cpython(
                source, inputs=inputs, capture_globals=capture_globals, timeout=timeout
            )

        if state is OptState.WARM:
            self.warmup(source, inputs, n=3)
            return run_cpython(
                source, inputs=inputs, capture_globals=capture_globals, timeout=timeout
            )

        if state is OptState.HOT:
            self.warmup(source, inputs, n=100)
            return run_cpython(
                source, inputs=inputs, capture_globals=capture_globals, timeout=timeout
            )

        if state is OptState.VERY_HOT:
            self.warmup(source, inputs, n=10_000)
            return run_cpython(
                source, inputs=inputs, capture_globals=capture_globals, timeout=timeout
            )

        if state is OptState.DEOPT:
            self.warmup(source, inputs, n=100)
            self.force_deopt(source, inputs)
            return run_cpython(
                source, inputs=inputs, capture_globals=capture_globals, timeout=timeout
            )

        if state is OptState.REHEATED:
            self.warmup(source, inputs, n=100)
            self.force_deopt(source, inputs)
            self.warmup(source, inputs, n=100)
            return run_cpython(
                source, inputs=inputs, capture_globals=capture_globals, timeout=timeout
            )

        raise ValueError(f"unknown opt_state: {state!r}")


@dataclass
class WarmupProfile:
    """Description of how a particular test should be warmed up."""

    cold_reps: int = 1
    warm_reps: int = 3
    hot_reps: int = 100
    very_hot_reps: int = 10_000
    deopt_after_warmup: bool = False
    reheat_after_deopt: bool = False

    @classmethod
    def for_state(cls, state: OptState | str) -> "WarmupProfile":
        s = OptState(state) if isinstance(state, str) else state
        if s is OptState.COLD:
            return cls(cold_reps=1)
        if s is OptState.WARM:
            return cls(cold_reps=1, warm_reps=3)
        if s is OptState.HOT:
            return cls(cold_reps=1, warm_reps=3, hot_reps=100)
        if s is OptState.VERY_HOT:
            return cls(cold_reps=1, warm_reps=3, hot_reps=100, very_hot_reps=10_000)
        if s is OptState.DEOPT:
            return cls(cold_reps=1, warm_reps=3, hot_reps=100, deopt_after_warmup=True)
        if s is OptState.REHEATED:
            return cls(
                cold_reps=1,
                warm_reps=3,
                hot_reps=100,
                deopt_after_warmup=True,
                reheat_after_deopt=True,
            )
        raise ValueError(f"unknown opt_state: {s!r}")
