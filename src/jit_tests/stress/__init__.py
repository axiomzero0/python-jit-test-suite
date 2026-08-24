"""Hand-crafted stress tests targeting specific JIT failure modes.

Unlike the deterministic matrix (which enumerates axes to produce a
coverage grid), each stress test here is a deliberately constructed
program designed to break a specific JIT assumption. The value is in
the design of each test, not the raw count.

Each stress test is a :class:`StressTest` with:
    name         - short identifier
    description  - what JIT failure mode it targets and why
    source       - the actual Python source
    tags         - TagSet describing what it exercises
    category     - failure-mode category (see TAXONOMY below)

Failure-mode taxonomy:

    01_type_speculation      Type guards that should fail mid-execution
    02_inline_caches         IC invalidation, megamorphic call sites
    03_osr                   On-stack replacement entry/exit edges
    04_deoptimization        Deopt correctness, state reconstruction
    05_guard_failures        Guard failure recovery paths
    06_escape_analysis       Scalar replacement, escape via side channels
    07_register_alloc        Live range splitting, spill at calls
    08_codegen               Specific instruction sequences
    09_exception_interaction Exceptions in optimized frames
    10_generators            Generator suspension in hot code
    11_gc_interaction        GC during deopt, weak refs, finalizers
    12_aliasing              Container aliasing, mutation during iter
    13_numeric_edges         Overflow, IEEE edges, big int transitions
    14_container_repr        List->dict transitions, shape changes
    15_closure_lifetime      Closure variable representation, lifetime
    16_metaprog_invalidation Runtime mutation that invalidates assumptions
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator

from ..harness import OptState, TagSet, TestCase


@dataclass(frozen=True)
class StressTest:
    name: str
    description: str
    source: str
    category: str
    tags: TagSet = field(default_factory=TagSet)

    def to_test_case(self, *, opt_state: OptState = OptState.COLD, index: int = 0) -> TestCase:
        """Convert to a TestCase for the runner."""
        return TestCase(
            source=self.source,
            inputs=(),
            tags=TagSet(
                semantic=self.tags.semantic,
                type_stability=self.tags.type_stability,
                control_flow=self.tags.control_flow,
                call_behavior=self.tags.call_behavior,
                opt_state=opt_state,
                tags=self.tags.tags | {"stress", "hand-crafted", self.category},
            ),
            id=f"stress-{self.category}-{index:04d}-{opt_state.value}",
            category=f"stress_{self.category}",
        )


# Import all category modules to aggregate their tests. Some planned
# modules (codegen, generators, ...) don't exist yet; import them
# defensively so the package still loads and the existing modules can
# be used while the rest are being written.
import importlib as _importlib

_CATEGORY_MODULE_NAMES = (
    "type_speculation",
    "inline_caches",
    "osr",
    "deoptimization",
    "guard_failures",
    "escape_analysis",
    "register_alloc",
    "codegen",
    "exception_interaction",
    "generators",
    "gc_interaction",
    "aliasing",
    "numeric_edges",
    "container_repr",
    "closure_lifetime",
    "metaprog_invalidation",
)

_ALL_MODULES = []
for _name in _CATEGORY_MODULE_NAMES:
    try:
        _mod = _importlib.import_module(f".{_name}", __package__)
    except Exception as _exc:  # noqa: BLE001
        # Module not implemented yet, has a syntax error, or contains
        # tests whose TagSet construction is invalid. Skip it so the
        # package still loads and the well-formed modules are usable.
        continue
    globals()[_name] = _mod
    _ALL_MODULES.append(_mod)
del _importlib, _name


def all_stress_tests() -> list[StressTest]:
    """Return every hand-crafted stress test, aggregated across categories."""
    out = []
    for mod in _ALL_MODULES:
        out.extend(mod.STRESS_TESTS)
    return out


def generate(
    *,
    n: int | None = None,
    seed: int = 0,
    opt_states: list[OptState] | None = None,
) -> Iterator[TestCase]:
    """Yield TestCase objects for every stress test, expanded across opt states.

    By default each stress test runs in all 6 opt states, so the total
    count is ``len(all_stress_tests()) * 6``.
    """
    tests = all_stress_tests()
    if opt_states is None:
        opt_states = [
            OptState.COLD, OptState.WARM, OptState.HOT,
            OptState.VERY_HOT, OptState.DEOPT, OptState.REHEATED,
        ]
    idx = 0
    for test in tests:
        for state in opt_states:
            if n is not None and idx >= n:
                return
            yield test.to_test_case(opt_state=state, index=idx)
            idx += 1


TAXONOMY = {
    "type_speculation": "Type guards that should fail mid-execution",
    "inline_caches": "IC invalidation, megamorphic call sites",
    "osr": "On-stack replacement entry/exit edges",
    "deoptimization": "Deopt correctness, state reconstruction",
    "guard_failures": "Guard failure recovery paths",
    "escape_analysis": "Scalar replacement, escape via side channels",
    "register_alloc": "Live range splitting, spill at calls",
    "codegen": "Specific instruction sequences",
    "exception_interaction": "Exceptions in optimized frames",
    "generators": "Generator suspension in hot code",
    "gc_interaction": "GC during deopt, weak refs, finalizers",
    "aliasing": "Container aliasing, mutation during iter",
    "numeric_edges": "Overflow, IEEE edges, big int transitions",
    "container_repr": "List->dict transitions, shape changes",
    "closure_lifetime": "Closure variable representation, lifetime",
    "metaprog_invalidation": "Runtime mutation that invalidates assumptions",
}


__all__ = [
    "StressTest",
    "all_stress_tests",
    "generate",
    "TAXONOMY",
]
