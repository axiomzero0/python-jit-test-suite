"""Tag system for classifying tests along multiple axes.

Every test carries a TagSet; the harness uses these to slice the matrix
(e.g. "run only numeric / monomorphic / very hot" or "find all tests
that exercise deoptimization").

Axes (canonical string values):

    semantic_axis:
        language_semantics | numeric | objects | containers | strings |
        functions | exceptions | metaprogramming | memory_gc | concurrency |
        ml_kernels | real_world | interpreter_tiers

    type_stability:
        monomorphic | bimorphic | polymorphic | megamorphic | unknown

    control_flow:
        straight_line | if_else | nested_branch | loop | nested_loop |
        irreducible | early_exit | break_continue | recursion |
        mutual_recursion

    call_behavior:
        direct | indirect | method | builtin | py_to_py | py_to_native |
        native_to_py | recursive | closure | generator | async

    opt_state:
        cold | warm | hot | very_hot | deoptimized | reheated

    tags (free-form set):
        e.g. {"vectorization", "specialization", "deoptimization",
              "OSR", "inline-cache", "escape-analysis", "regalloc",
              "codegen", "GC", "IC-miss", "guard-failure", "exception"}
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable


class Semantic(str, Enum):
    LANGUAGE = "language_semantics"
    NUMERIC = "numeric"
    OBJECTS = "objects"
    CONTAINERS = "containers"
    STRINGS = "strings"
    FUNCTIONS = "functions"
    EXCEPTIONS = "exceptions"
    METAPROGRAMMING = "metaprogramming"
    MEMORY_GC = "memory_gc"
    CONCURRENCY = "concurrency"
    ML_KERNELS = "ml_kernels"
    REAL_WORLD = "real_world"
    INTERPRETER_TIERS = "interpreter_tiers"
    # Stress tests form their own semantic group: every hand-crafted test
    # under ``jit_tests.stress`` is classified with ``semantic="stress"``.
    STRESS = "stress"


class TypeStability(str, Enum):
    MONO = "monomorphic"
    BI = "bimorphic"
    POLY = "polymorphic"
    MEGA = "megamorphic"
    UNKNOWN = "unknown"


class ControlFlow(str, Enum):
    STRAIGHT = "straight_line"
    IF_ELSE = "if_else"
    NESTED_BRANCH = "nested_branch"
    LOOP = "loop"
    NESTED_LOOP = "nested_loop"
    IRREDUCIBLE = "irreducible"
    EARLY_EXIT = "early_exit"
    BREAK_CONTINUE = "break_continue"
    RECURSION = "recursion"
    MUTUAL_RECURSION = "mutual_recursion"


class CallBehavior(str, Enum):
    DIRECT = "direct"
    INDIRECT = "indirect"
    METHOD = "method"
    BUILTIN = "builtin"
    PY_TO_PY = "py_to_py"
    PY_TO_NATIVE = "py_to_native"
    NATIVE_TO_PY = "native_to_py"
    RECURSIVE = "recursive"
    CLOSURE = "closure"
    GENERATOR = "generator"
    ASYNC = "async"


class OptState(str, Enum):
    COLD = "cold"
    WARM = "warm"
    HOT = "hot"
    VERY_HOT = "very_hot"
    DEOPT = "deoptimized"
    REHEATED = "reheated"


@dataclass(frozen=True)
class TagSet:
    semantic: Semantic = Semantic.LANGUAGE
    type_stability: TypeStability = TypeStability.UNKNOWN
    control_flow: ControlFlow = ControlFlow.STRAIGHT
    call_behavior: CallBehavior = CallBehavior.DIRECT
    opt_state: OptState = OptState.COLD
    tags: frozenset[str] = field(default_factory=frozenset)

    @classmethod
    def make(
        cls,
        semantic: str | Semantic = "language_semantics",
        *,
        type_stability: str | TypeStability = "unknown",
        control_flow: str | ControlFlow = "straight_line",
        call_behavior: str | CallBehavior = "direct",
        opt_state: str | OptState = "cold",
        tags: Iterable[str] | None = None,
    ) -> "TagSet":
        return cls(
            semantic=Semantic(semantic) if not isinstance(semantic, Semantic) else semantic,
            type_stability=(
                TypeStability(type_stability)
                if not isinstance(type_stability, TypeStability)
                else type_stability
            ),
            control_flow=(
                ControlFlow(control_flow)
                if not isinstance(control_flow, ControlFlow)
                else control_flow
            ),
            call_behavior=(
                CallBehavior(call_behavior)
                if not isinstance(call_behavior, CallBehavior)
                else call_behavior
            ),
            opt_state=(
                OptState(opt_state) if not isinstance(opt_state, OptState) else opt_state
            ),
            tags=frozenset(tags or ()),
        )

    def as_dict(self) -> dict[str, str | list[str]]:
        return {
            "semantic": self.semantic.value,
            "type_stability": self.type_stability.value,
            "control_flow": self.control_flow.value,
            "call_behavior": self.call_behavior.value,
            "opt_state": self.opt_state.value,
            "tags": sorted(self.tags),
        }
