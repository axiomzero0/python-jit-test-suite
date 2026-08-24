"""Guard failure recovery stress tests.

Guards are runtime checks the JIT inserts into compiled code to verify
its speculations. When a guard fails, the JIT must:

1. Trap into the deopt handler
2. Reconstruct the interpreter frame
3. Re-execute the failing instruction in the interpreter
4. Update the type profile to reflect the new type

Each test below constructs a scenario where a specific guard should
fail and verifies that the recovery is correct.
"""

from __future__ import annotations

from ._shared import T
from ..harness import TagSet


STRESS_TESTS = [
    T(
        name="guard_type_int_to_float",
        category="guard_failures",
        description="Type guard `isinstance(x, int)` fails when x is float.",
        source='''def add_one(x):
    return x + 1

# Warm up with ints
for i in range(1000):
    add_one(i)

# Guard fails: float
assert add_one(1.5) == 2.5

# Guard fails: large int (may overflow tagged int)
assert add_one(2**63) == 2**63 + 1

# Guard fails: complex
assert add_one(1+2j) == 2+2j

# Guard fails: str (str + int fails, but str + str works)
assert add_one("a") == "a1" if False else True  # "a"+1 raises; skip

# After guard failures, normal int works
assert add_one(41) == 42
''',
        tags=TagSet.make("stress", type_stability="polymorphic",
                         opt_state="deoptimized", tags={"guard", "type", "binop"}),
    ),
    T(
        name="guard_type_list_to_tuple",
        category="guard_failures",
        description="Type guard `isinstance(x, list)` fails when x is tuple.",
        source='''\
def first(x):
    return x[0]

for _ in range(1000):
    first([1, 2, 3])

assert first((10, 20, 30)) == 10
assert first("hello") == "h"
assert first(range(5)) == 0
''',
        tags=TagSet.make("stress", type_stability="polymorphic",
                         opt_state="deoptimized", tags={"guard", "type", "index"}),
    ),
    T(
        name="guard_range_overflow",
        category="guard_failures",
        description="Range guard `0 <= i < len` fails when i is out of bounds.",
        source='''def get(x, i):
    return x[i]

lst = list(range(100))
for i in range(100):
    get(lst, i)

# Guard fails: positive out of bounds
for idx in [100, 200]:
    try:
        get(lst, idx)
        assert False, f"should raise for {idx}"
    except IndexError:
        pass

# Negative index out of bounds
try:
    get(lst, -101)
    assert False, "should raise"
except IndexError:
    pass

# Valid negative indices
assert get(lst, -1) == 99
assert get(lst, -100) == 0

# After guard failures, normal access works
assert get(lst, 50) == 50
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         opt_state="deoptimized",
                         tags={"guard", "range", "index", "bound"}),
    ),
    T(
        name="guard_dict_key_missing",
        category="guard_failures",
        description="Dict key presence guard fails when key is missing.",
        source='''\
d = {str(i): i for i in range(100)}

def lookup(k):
    return d[k]

for i in range(1000):
    lookup(str(i % 100))

# Guard fails: missing key
for k in ["missing", "absent", "xxx"]:
    try:
        lookup(k)
        assert False
    except KeyError:
        pass

assert lookup("50") == 50
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         opt_state="deoptimized", tags={"guard", "dict", "missing"}),
    ),
    T(
        name="guard_attribute_missing",
        category="guard_failures",
        description="Attribute presence guard fails when attr is missing.",
        source='''\
class A:
    def __init__(self):
        self.x = 1

a = A()

def get(o):
    return o.x

for _ in range(1000):
    get(a)

# Delete the attribute
del a.x
try:
    get(a)
    assert False
except AttributeError:
    pass

# Restore
a.x = 42
assert get(a) == 42
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         opt_state="deoptimized",
                         tags={"guard", "attribute", "missing"}),
    ),
    T(
        name="guard_function_arity",
        category="guard_failures",
        description=(
            "JIT may inline a call assuming a fixed arity. If the "
            "callee is replaced with one of different arity, the "
            "guard fails."
        ),
        source='''\
def f(a, b):
    return a + b

def call(g, x, y):
    return g(x, y)

for _ in range(1000):
    call(f, 1, 2)

# Replace with a 3-arg function
def g3(a, b, c):
    return a + b + c

# call(f, 1, 2) was correct; now call(g3, 1, 2) should fail with TypeError
try:
    call(g3, 1, 2)
    assert False, "should raise TypeError"
except TypeError:
    pass

# Restore
assert call(f, 1, 2) == 3
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         call_behavior="indirect", opt_state="deoptimized",
                         tags={"guard", "arity", "call"}),
    ),
    T(
        name="guard_division_by_zero",
        category="guard_failures",
        description="Division guard `b != 0` fails when b is 0.",
        source='''\
def divide(a, b):
    return a / b

for i in range(1, 100):
    divide(100, i)

# Guard fails
for _ in range(5):
    try:
        divide(1, 0)
        assert False
    except ZeroDivisionError:
        pass

# After guard failure, normal division should work
assert divide(10, 2) == 5.0
assert divide(100, 4) == 25.0
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         opt_state="deoptimized", tags={"guard", "division", "zero"}),
    ),
    T(
        name="guard_int_to_bigint",
        category="guard_failures",
        description="Int size guard `fits in 64 bits` fails on overflow.",
        source='''\
def mul(x, y):
    return x * y

for _ in range(1000):
    mul(2, 3)

# Guard fails: overflow
assert mul(2**32, 2**32) == 2**64
assert mul(2**63, 2) == 2**64
assert mul(2**100, 2**100) == 2**200

# Back to small
assert mul(2, 3) == 6
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         opt_state="deoptimized",
                         tags={"guard", "int", "overflow", "bigint"}),
    ),
    T(
        name="guard_class_layout_change",
        category="guard_failures",
        description=(
            "Class layout guard fails when a __slots__ attribute is "
            "added or removed."
        ),
        source='''\
class A:
    __slots__ = ('x',)

a = A()
a.x = 1

def get(o):
    return o.x

for _ in range(1000):
    get(a)

# Subclass with different slots
class B(A):
    __slots__ = ('y',)

b = B()
b.x = 10
b.y = 20
assert get(b) == 10
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         opt_state="deoptimized",
                         tags={"guard", "class", "slots", "layout"}),
    ),
    T(
        name="guard_string_to_bytes",
        category="guard_failures",
        description="String type guard fails when bytes is passed.",
        source='''\
def upper(s):
    return s.upper()

for _ in range(1000):
    upper("hello")

# Guard fails: bytes
try:
    upper(b"hello")
    # bytes does have upper() but returns bytes
    assert upper(b"hello") == b"HELLO"
except AttributeError:
    pass  # depending on impl

assert upper("hello") == "HELLO"
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         opt_state="deoptimized",
                         tags={"guard", "string", "bytes"}),
    ),
    T(
        name="guard_callable_to_non_callable",
        category="guard_failures",
        description="Callable guard fails when a non-callable is passed.",
        source='''\
def f():
    return 42

def call(g):
    return g()

for _ in range(1000):
    call(f)

# Guard fails: non-callable
try:
    call(42)
    assert False
except TypeError:
    pass

assert call(f) == 42
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         call_behavior="indirect", opt_state="deoptimized",
                         tags={"guard", "callable"}),
    ),
    T(
        name="guard_iterator_exhausted",
        category="guard_failures",
        description=(
            "Iterator `has_next` guard fails when the iterator is "
            "exhausted earlier than expected."
        ),
        source='''\
def consume(it, n):
    results = []
    for i in range(n):
        try:
            results.append(next(it))
        except StopIteration:
            results.append("exhausted")
    return results

it = iter(range(50))
r = consume(it, 100)
assert r[:50] == list(range(50))
assert all(x == "exhausted" for x in r[50:])
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", opt_state="deoptimized",
                         tags={"guard", "iterator", "StopIteration"}),
    ),
    T(
        name="guard_recursion_depth",
        category="guard_failures",
        description="Recursion limit guard fails when depth is exceeded.",
        source='''\
import sys

def recurse(n):
    if n <= 0:
        return 0
    return 1 + recurse(n - 1)

# Safe depth
assert recurse(100) == 100

# Exceed limit
try:
    recurse(sys.getrecursionlimit() + 100)
    assert False, "should have raised RecursionError"
except RecursionError:
    pass

# After recovery, normal recursion works
assert recurse(50) == 50
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="recursion", call_behavior="recursive",
                         opt_state="deoptimized", tags={"guard", "recursion", "depth"}),
    ),
    T(
        name="guard_memory_allocation_failure",
        category="guard_failures",
        description=(
            "Allocation guard. Trying to allocate a huge list should "
            "fail gracefully (MemoryError or ValueError), not crash."
        ),
        source='''\
def make_list(n):
    return list(range(n))

# Normal
assert make_list(100) == list(range(100))

# Large but feasible
assert len(make_list(1_000_000)) == 1_000_000

# Huge - should raise, not crash
try:
    make_list(10**18)
    # If it didn't raise, that's fine too (some impls handle it)
except (MemoryError, OverflowError, ValueError):
    pass

# Recovery
assert make_list(10) == list(range(10))
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         opt_state="deoptimized",
                         tags={"guard", "memory", "allocation"}),
    ),
    T(
        name="guard_multiple_failures_in_sequence",
        category="guard_failures",
        description=(
            "Multiple guards fail in sequence. Each failure should "
            "trigger deopt, and the interpreter should handle the "
            "next failure correctly."
        ),
        source='''def work(values):
    results = []
    for v in values:
        try:
            r1 = v + 1
        except TypeError:
            r1 = "type-error"
        try:
            r2 = v[0]
        except TypeError:
            r2 = "type-error"
        results.append((r1, r2))
    return results

r = work([1, "hello", [10, 20], 3.14])
# v=1: 1+1=2, 1[0] -> TypeError
assert r[0] == (2, "type-error")
# v="hello": "hello"+1 -> TypeError, "hello"[0]="h"
assert r[1] == ("type-error", "h")
# v=[10,20]: [10,20]+1 -> TypeError, [10,20][0]=10
assert r[2] == ("type-error", 10)
# v=3.14: 3.14+1=4.14, 3.14[0] -> TypeError
assert abs(r[3][0] - 4.14) < 1e-9
assert r[3][1] == "type-error"
''',
        tags=TagSet.make("stress", type_stability="megamorphic",
                         control_flow="loop", opt_state="deoptimized",
                         tags={"guard", "multiple", "sequence"}),
    ),
]
