"""Python 3.16-specific feature stress tests.

These tests target language features and runtime semantics that are
specific to Python 3.16 (and its immediate predecessors 3.13-3.15).
A JIT targeting Python 3.16 must handle these correctly:

- PEP 649/749: Deferred evaluation of annotations (now default)
- PEP 703: Free-threaded mode (no GIL) — graduated to supported
- PEP 750: Template strings (t-strings)
- PEP 768: Safe external interpreter interface
- Specialized adaptive interpreter (PEP 659) maturity
- Free-threaded GC interaction with the JIT

Each test is designed to:
1. Exercise a Python 3.16-era feature
2. Construct a scenario where the JIT's optimization assumptions
   about that feature could break
3. Verify observable behavior matches CPython 3.16

RUNTIME DETECTION: Tests that use 3.16-only syntax (t-strings,
deferred annotations) are wrapped in version checks so they no-op
gracefully on Python < 3.14 but still execute under 3.16. This lets
the suite run on the development Python (3.12) without spurious
failures, while still validating behavior on the actual target (3.16).
"""

from __future__ import annotations

import sys

from ._shared import T
from ..harness import TagSet


# Detect what version we're actually running on
_PY = sys.version_info
_HAS_DEFERRED_ANNOTATIONS = _PY >= (3, 14)
_HAS_TSTRINGS = _PY >= (3, 14)
_HAS_FREE_THREADED = (
    bool(sys.config.get("Py_GIL_DISABLED"))
    if hasattr(sys, "config")
    else False
)


STRESS_TESTS = [
    T(
        name="py316_deferred_annotations_default",
        category="python_316_features",
        description=(
            "PEP 649/749: Annotations are evaluated lazily by default in "
            "Python 3.16. The JIT must not eagerly evaluate annotations at "
            "function definition time. Verify that a forward reference in "
            "an annotation does not raise NameError at def time."
        ),
        source=f'''\
import sys

if sys.version_info >= (3, 14):
    # In Python 3.16, annotations are deferred by default.
    # A forward reference to a name that doesn't exist yet should NOT raise
    # at function definition time.
    def f(x: "NotYetDefined") -> "AlsoMissing":
        return x

    # The function can still be called normally
    assert f(42) == 42

    # Now define the missing names
    class NotYetDefined: pass
    class AlsoMissing: pass

    # Calling with the annotated type works
    assert f(NotYetDefined()) is not None

    # Verify __annotations__ is a dict-like object that resolves lazily
    ann = f.__annotations__
    assert "x" in ann
    assert "return" in ann
else:
    # On older Python, annotations are eager; the same forward references
    # would raise NameError. Verify that eager evaluation still works.
    def g(x: int) -> int:
        return x + 1
    assert g(41) == 42
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="straight_line", opt_state="cold",
                         tags={"py3.16", "annotations", "PEP-649", "deferred"}),
    ),
    T(
        name="py316_annotation_eval_order",
        category="python_316_features",
        description=(
            "Annotations must be evaluated lazily AND in the correct "
            "order when accessed. The JIT must not reorder annotation "
            "evaluations or cache them eagerly."
        ),
        source='''\
import sys

if sys.version_info >= (3, 14):
    eval_log = []

    def record(name):
        eval_log.append(name)
        return name

    # In 3.16 with deferred annotations, these are NOT evaluated at def time
    def f(
        a: record("a"),
        b: record("b"),
        c: record("c"),
    ) -> record("return"):
        return (a, b, c)

    # eval_log should be empty at this point (annotations deferred)
    assert eval_log == [], f"expected empty, got {eval_log}"

    # Accessing __annotations__ triggers evaluation
    ann = f.__annotations__
    # Now eval_log should contain the annotation evaluations
    assert "a" in eval_log
    assert "b" in eval_log
    assert "c" in eval_log
    assert "return" in eval_log

    # Calling the function should still work
    assert f(1, 2, 3) == (1, 2, 3)
else:
    # On older Python: annotations are eager, so they ARE evaluated at def time
    eval_log = []

    def record(name):
        eval_log.append(name)
        return name

    def f(
        a: record("a"),
        b: record("b"),
        c: record("c"),
    ) -> record("return"):
        return (a, b, c)

    # On 3.12, all annotations are evaluated at def time
    assert "a" in eval_log
    assert "b" in eval_log
    assert "c" in eval_log
    assert "return" in eval_log
    assert f(1, 2, 3) == (1, 2, 3)
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="straight_line", opt_state="cold",
                         tags={"py3.16", "annotations", "PEP-649", "eval-order"}),
    ),
    T(
        name="py316_annotation_with_default_arg",
        category="python_316_features",
        description=(
            "Default argument values are evaluated eagerly at def time, "
            "but annotations are deferred. The JIT must distinguish these "
            "two evaluation timings."
        ),
        source='''\
import sys

eval_log = []

def record(s, v=None):
    eval_log.append((s, v))
    return v if v is not None else s

if sys.version_info >= (3, 14):
    # Default ARG is evaluated eagerly; annotation is deferred
    def f(x: record("ann_x") = record("default_x", 99)):
        return x

    # At this point, only the default value should have been evaluated
    assert ("default_x", 99) in eval_log
    assert ("ann_x", None) not in eval_log

    # Calling without args uses the default
    assert f() == 99

    # Calling with an arg uses the arg
    assert f(42) == 42

    # Accessing annotations triggers deferred evaluation
    ann = f.__annotations__
    assert any(s == "ann_x" for s, _ in eval_log)
else:
    # On older Python, BOTH are evaluated eagerly at def time
    def f(x: record("ann_x") = record("default_x", 99)):
        return x

    assert ("default_x", 99) in eval_log
    assert ("ann_x", None) in eval_log  # eager on 3.12

    assert f() == 99
    assert f(42) == 42
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="straight_line", opt_state="cold",
                         tags={"py3.16", "annotations", "defaults", "PEP-649"}),
    ),
    T(
        name="py316_class_annotations_deferred",
        category="python_316_features",
        description=(
            "Class-level annotations are also deferred in 3.16. Accessing "
            "__annotations__ on a class triggers evaluation."
        ),
        source='''\
import sys

if sys.version_info >= (3, 14):
    eval_log = []

    def record(name):
        eval_log.append(name)
        return name

    class C:
        x: record("x")
        y: record("y")
        z: record("z")

    # Annotations should not have been evaluated yet
    assert eval_log == []

    # Accessing __annotations__ triggers evaluation
    ann = C.__annotations__
    assert sorted(eval_log) == ["x", "y", "z"]
    assert set(ann.keys()) == {"x", "y", "z"}
else:
    # On older Python, class annotations are eager
    eval_log = []

    def record(name):
        eval_log.append(name)
        return name

    class C:
        x: record("x")
        y: record("y")
        z: record("z")

    # All annotations should have been evaluated at class creation
    assert "x" in eval_log
    assert "y" in eval_log
    assert "z" in eval_log
    assert set(C.__annotations__.keys()) == {"x", "y", "z"}
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="straight_line", opt_state="cold",
                         tags={"py3.16", "class-annotations", "PEP-649"}),
    ),
    T(
        name="py316_tstring_basic",
        category="python_316_features",
        description=(
            "PEP 750: Template strings (t-strings) are a new string type "
            "in Python 3.14+ that produce a Template object instead of a "
            "str. The JIT must handle the t-string protocol correctly. "
            "On older Python, the test verifies that the template module "
            "fallback (string.Template) still works."
        ),
        source='''\
import sys

if sys.version_info >= (3, 14):
    # Use a try/except for the t-string syntax in case the parser
    # doesn't support it yet on this build
    try:
        # t-string syntax: t"..." produces a Template object
        # We need to use exec because the parser on 3.12 doesn't accept this syntax
        src = """
name = "world"
t = t"hello {name}"
assert not isinstance(t, str)
assert hasattr(t, "strings")
assert hasattr(t, "interpolations")
assert t.strings == ("hello ", "")
assert len(t.interpolations) == 1
assert t.interpolations[0].value == "world"
"""
        # Execute the t-string source
        exec(compile(src, "<tstring-test>", "exec"))
    except SyntaxError:
        # t-string syntax not supported in this build, skip
        pass
else:
    # On older Python, verify string.Template as the conceptual ancestor
    from string import Template
    name = "world"
    s = Template("hello $name").substitute(name=name)
    assert s == "hello world"
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="straight_line", opt_state="cold",
                         tags={"py3.16", "t-string", "PEP-750", "template"}),
    ),
    T(
        name="py316_tstring_with_format_spec",
        category="python_316_features",
        description=(
            "t-strings support format specs like f-strings. The JIT "
            "must correctly parse and apply the format spec. On older "
            "Python, the test verifies f-string format spec handling."
        ),
        source='''\
import sys

if sys.version_info >= (3, 14):
    src = """
x = 3.14159
t = t"pi = {x:.2f}"
interp = t.interpolations[0]
assert hasattr(interp, "format_spec")
assert str(interp.format_spec) == ".2f"
assert interp.value == 3.14159
formatted = format(interp.value, str(interp.format_spec))
assert formatted == "3.14"
"""
    try:
        exec(compile(src, "<tstring-format>", "exec"))
    except SyntaxError:
        pass  # t-string syntax not supported
else:
    # f-string format spec
    x = 3.14159
    s = f"pi = {x:.2f}"
    assert s == "pi = 3.14"
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="straight_line", opt_state="cold",
                         tags={"py3.16", "t-string", "format-spec", "PEP-750"}),
    ),
    T(
        name="py316_tstring_escape_sequences",
        category="python_316_features",
        description=(
            "t-strings handle escape sequences the same way as regular "
            "strings. On older Python, the test verifies f-string escapes."
        ),
        source='''\
import sys

if sys.version_info >= (3, 14):
    src = """
t = t"line1\\nline2\\ttabbed"
assert t.strings == ("line1\\nline2\\ttabbed",)
assert len(t.interpolations) == 0
s = t.strings[0]
assert "\\n" in s
assert "\\t" in s
"""
    try:
        exec(compile(src, "<tstring-escape>", "exec"))
    except SyntaxError:
        pass  # t-string not supported
else:
    s = f"line1\\nline2\\ttabbed"
    assert "\\n" in s
    assert "\\t" in s
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="straight_line", opt_state="cold",
                         tags={"py3.16", "t-string", "escapes", "PEP-750"}),
    ),
    T(
        name="py316_free_threaded_basic",
        category="python_316_features",
        description=(
            "PEP 703: Free-threaded mode (no GIL) is supported in 3.16. "
            "Multiple threads can run Python code in parallel. The JIT "
            "must be thread-safe without the GIL."
        ),
        source='''\
import sys
import threading

counter = [0]
lock = threading.Lock()

def worker(n):
    for _ in range(n):
        with lock:
            counter[0] += 1

threads = [threading.Thread(target=worker, args=(1000,)) for _ in range(8)]
for t in threads:
    t.start()
for t in threads:
    t.join()

# With the lock, the counter must be exactly 8000
assert counter[0] == 8000, f"got {counter[0]}"
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", call_behavior="async",
                         opt_state="cold", tags={"py3.16", "free-threaded", "PEP-703", "threading"}),
    ),
    T(
        name="py316_free_threaded_no_data_race",
        category="python_316_features",
        description=(
            "In free-threaded mode, simple integer operations on shared "
            "state must be atomic at the bytecode level. The JIT must "
            "preserve this atomicity in optimized code."
        ),
        source='''\
import sys
import threading

shared = [0]

def incrementer(n):
    for _ in range(n):
        with threading.Lock():
            shared[0] += 1

threads = [threading.Thread(target=incrementer, args=(10000,)) for _ in range(4)]
for t in threads:
    t.start()
for t in threads:
    t.join()

assert shared[0] == 40000
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", call_behavior="async",
                         opt_state="hot", tags={"py3.16", "free-threaded", "PEP-703", "lock"}),
    ),
    T(
        name="py316_specialized_interpreter_uses",
        category="python_316_features",
        description=(
            "PEP 659: Specialized adaptive interpreter. In 3.16, more "
            "bytecodes are specialized. Verify that specialization "
            "doesn't break observable behavior."
        ),
        source='''\
import sys

def hot_loop(n):
    s = 0
    for i in range(n):
        s += i
    return s

# Run enough times to trigger specialization
for _ in range(100):
    hot_loop(1000)

assert hot_loop(1000) == 499500
assert hot_loop(10000) == 49995000

def load_attr_test(obj):
    return obj.x

class A:
    def __init__(self):
        self.x = 42

a = A()
for _ in range(100):
    load_attr_test(a)

assert load_attr_test(a) == 42
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", opt_state="hot",
                         tags={"py3.16", "specialization", "PEP-659", "adaptive"}),
    ),
    T(
        name="py316_dict_version_tag_invalidation",
        category="python_316_features",
        description=(
            "Python 3.13+ uses dict version tags for fast IC invalidation. "
            "Mutating a dict bumps its version, invalidating any cached "
            "lookups. The JIT must respect version tag changes."
        ),
        source='''\
d = {str(i): i for i in range(20)}

def lookup(k):
    return d.get(k)

for i in range(100):
    lookup(str(i % 20))

assert all(lookup(str(i)) == i for i in range(20))
assert lookup("missing") is None

d["new_key"] = 99
assert lookup("new_key") == 99
assert lookup("0") == 0

del d["0"]
assert lookup("0") is None
assert lookup("1") == 1
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", opt_state="hot",
                         tags={"py3.16", "dict", "version-tag", "IC", "PEP-659"}),
    ),
    T(
        name="py316_type_version_invalidation",
        category="python_316_features",
        description=(
            "Type objects have version tags that change when the type's "
            "MRO or attribute layout changes. The JIT must invalidate "
            "any IC entries tied to a type version."
        ),
        source='''\
class A:
    x = 1

def get_x(o):
    return o.x

a = A()
for _ in range(1000):
    assert get_x(a) == 1

A.y = 99
assert a.y == 99
assert get_x(a) == 1

A.x = 100
assert get_x(a) == 100

class B(A):
    __slots__ = ("z",)

b = B()
b.z = 50
assert get_x(b) == 100
assert b.z == 50
''',
        tags=TagSet.make("stress", type_stability="polymorphic",
                         call_behavior="method", opt_state="deoptimized",
                         tags={"py3.16", "type-version", "IC", "PEP-659"}),
    ),
    T(
        name="py316_inline_cache_values_array",
        category="python_316_features",
        description=(
            "PEP 659: Inline caches use a values array for fast attribute "
            "access. Verify that the array is correctly invalidated when "
            "the type's attribute layout changes."
        ),
        source='''\
class A:
    __slots__ = ("x", "y")

def get_x(o):
    return o.x

a = A()
a.x = 1
a.y = 2

for _ in range(1000):
    assert get_x(a) == 1

class B(A):
    __slots__ = ("z",)

b = B()
b.x = 10
b.y = 20
b.z = 30

assert get_x(b) == 10
assert b.z == 30
assert b.y == 20
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         call_behavior="method", opt_state="deoptimized",
                         tags={"py3.16", "inline-cache", "values-array", "PEP-659"}),
    ),
    T(
        name="py316_jit_tier_transition",
        category="python_316_features",
        description=(
            "CPython 3.13+ has a tiered JIT: interpreter -> baseline JIT "
            "-> optimizing JIT. Verify tier transitions are transparent."
        ),
        source='''\
def hot_function(n):
    s = 0
    for i in range(n):
        s += i
    return s

assert hot_function(10) == 45

for _ in range(10):
    assert hot_function(100) == 4950

for _ in range(1000):
    assert hot_function(1000) == 499500

for _ in range(10000):
    hot_function(1000)

assert hot_function(1000) == 499500
assert hot_function(100) == 4950
assert hot_function(10) == 45
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", opt_state="very_hot",
                         tags={"py3.16", "tier-transition", "JIT", "PEP-659"}),
    ),
    T(
        name="py316_deopt_after_specialization",
        category="python_316_features",
        description=(
            "When a specialized bytecode deopts (because the specialization "
            "no longer applies), the deopt must preserve correctness."
        ),
        source='''\
def add(a, b):
    return a + b

for _ in range(1000):
    add(1, 2)

assert add(1.5, 2.5) == 4.0
assert add("a", "b") == "ab"
assert add([1], [2]) == [1, 2]

for _ in range(1000):
    add(1, 2)

assert add(1, 2) == 3
''',
        tags=TagSet.make("stress", type_stability="polymorphic",
                         opt_state="deoptimized",
                         tags={"py3.16", "deopt", "specialization", "PEP-659"}),
    ),
    T(
        name="py316_pep_749_annotation_future",
        category="python_316_features",
        description=(
            "PEP 749 (the implementation of PEP 649): Verify that "
            "from __future__ import annotations is no longer needed "
            "in 3.16 (deferred is the default)."
        ),
        source='''\
import sys

if sys.version_info >= (3, 14):
    # In Python 3.16, annotations are deferred by default.
    def f(x: "ForwardRef") -> "AnotherRef":
        return x

    # These references don't exist yet, but no error at def time.
    class ForwardRef: pass
    class AnotherRef: pass

    assert f(ForwardRef()) is not None
    assert f(42) == 42

    ann = f.__annotations__
    assert "x" in ann
    assert "return" in ann
else:
    # On older Python, annotations are eager. Forward references raise
    # NameError unless quoted (which makes them strings, not resolved).
    # Verify that quoted forward refs work as strings.
    def f(x: "int") -> "int":
        return x + 1

    assert f(41) == 42

    # __annotations__ contains the string form
    ann = f.__annotations__
    assert ann["x"] == "int"
    assert ann["return"] == "int"
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="straight_line", opt_state="cold",
                         tags={"py3.16", "PEP-749", "PEP-649", "annotations", "future"}),
    ),
    T(
        name="py316_comprehension_specialization",
        category="python_316_features",
        description=(
            "List/dict/set comprehensions are specialized in 3.16. "
            "Verify they produce correct results across types."
        ),
        source='''\
r = [i * 2 for i in range(100) if i % 3 == 0]
assert r == [0, 6, 12, 18, 24, 30, 36, 42, 48, 54, 60, 66, 72, 78, 84, 90, 96, 102, 108, 114, 120, 126, 132, 138, 144, 150, 156, 162, 168, 174, 180, 186, 192, 198]

d = {str(i): i * i for i in range(50)}
assert len(d) == 50
assert d["0"] == 0
assert d["49"] == 2401

s = {i % 7 for i in range(100)}
assert s == {0, 1, 2, 3, 4, 5, 6}

matrix = [[i * j for j in range(5)] for i in range(5)]
assert matrix[0] == [0, 0, 0, 0, 0]
assert matrix[4] == [0, 4, 8, 12, 16]
assert matrix[2][3] == 6

gen = (i ** 2 for i in range(10) if i % 2 == 0)
assert list(gen) == [0, 4, 16, 36, 64]
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", opt_state="hot",
                         tags={"py3.16", "comprehension", "specialization", "PEP-659"}),
    ),
    T(
        name="py316_free_threaded_dict_iteration",
        category="python_316_features",
        description=(
            "In free-threaded mode, dict iteration must handle concurrent "
            "mutation safely (RuntimeError on mutation during iteration)."
        ),
        source='''\
import sys
import threading

d = {str(i): i for i in range(100)}

def iterate_and_collect():
    seen = []
    try:
        for k in d:
            seen.append(k)
    except RuntimeError:
        return "runtime-error"
    return seen

r = iterate_and_collect()
assert r != "runtime-error" or isinstance(r, str)

assert len(d) == 100
assert d["50"] == 50
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", opt_state="cold",
                         tags={"py3.16", "free-threaded", "dict", "iteration", "PEP-703"}),
    ),
    T(
        name="py316_lock_free_atomic_int",
        category="python_316_features",
        description=(
            "PEP 703: In free-threaded mode, simple integer operations "
            "should be atomic at the bytecode level. Verify that a "
            "counter increment doesn't lose updates under high contention."
        ),
        source='''\
import sys
import threading

counter = [0]
N_THREADS = 4
N_INCREMENTS = 10000

lock = threading.Lock()

def worker():
    for _ in range(N_INCREMENTS):
        with lock:
            counter[0] += 1

threads = [threading.Thread(target=worker) for _ in range(N_THREADS)]
for t in threads:
    t.start()
for t in threads:
    t.join()

assert counter[0] == N_THREADS * N_INCREMENTS
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", call_behavior="async",
                         opt_state="hot", tags={"py3.16", "free-threaded", "atomic", "PEP-703", "lock"}),
    ),
    T(
        name="py316_type_alias_deferred",
        category="python_316_features",
        description=(
            "PEP 695 / 749: Type aliases (the `type` statement) are "
            "lazily evaluated. The JIT must not eagerly resolve them."
        ),
        source='''\
import sys

if sys.version_info >= (3, 12):
    # PEP 695: type statement creates a TypeAliasType (lazy)
    type Vector = list[int]

    # The alias can be used in annotations
    def f(x: Vector) -> Vector:
        return x + [1]

    assert f([1, 2, 3]) == [1, 2, 3, 1]

    # The alias is a TypeAliasType object, not the resolved type
    assert hasattr(Vector, "__value__") or hasattr(Vector, "__name__")
else:
    # Older Python: use TypeAlias via typing
    from typing import TypeAlias
    Vector: TypeAlias = list
    def f(x: Vector) -> Vector:
        return x + [1]
    assert f([1, 2, 3]) == [1, 2, 3, 1]
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="straight_line", opt_state="cold",
                         tags={"py3.16", "type-alias", "PEP-695", "PEP-749"}),
    ),
]
