"""Deoptimization correctness stress tests.

Deoptimization is the process of transferring execution from a
compiled frame back to the interpreter. The compiled frame must
reconstruct:

- The values of all locals (including unboxed values that need reboxing)
- The current position in the bytecode
- The exception state
- The block stack (try/except/finally frames)
- The type profile (so future re-optimization is informed)

Each test below constructs a scenario where deopt must happen and
verifies that the observable behavior matches the interpreter.
"""

from __future__ import annotations

from ._shared import T
from ..harness import TagSet


STRESS_TESTS = [
    T(
        name="deopt_preserves_int_sum_after_float",
        category="deoptimization",
        description=(
            "Loop accumulates ints. On iteration 500, a float is added. "
            "Deopt must convert `acc` from a tagged int to a Python "
            "float object."
        ),
        source='''\
def work():
    acc = 0
    for i in range(1000):
        if i == 500:
            acc += 0.5
        else:
            acc += i
    return acc

r = work()
assert r == sum(range(500)) + 0.5 + sum(range(501, 1000))
assert isinstance(r, float)
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         control_flow="loop", opt_state="deoptimized",
                         tags={"deopt", "unbox", "int-to-float"}),
    ),
    T(
        name="deopt_preserves_list_after_object",
        category="deoptimization",
        description=(
            "Loop appends ints to a list. On iteration 500, a string "
            "is appended. The list's element type spec must be "
            "invalidated."
        ),
        source='''\
def work():
    acc = []
    for i in range(1000):
        if i == 500:
            acc.append("string")
        else:
            acc.append(i)
    return acc

r = work()
assert len(r) == 1000
assert r[0] == 0
assert r[499] == 499
assert r[500] == "string"
assert r[501] == 501
assert r[-1] == 999
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         control_flow="loop", opt_state="deoptimized",
                         tags={"deopt", "list", "element-type"}),
    ),
    T(
        name="deopt_during_attribute_access",
        category="deoptimization",
        description=(
            "JIT speculates `o.x` is an instance dict lookup at offset "
            "N. Then `o.x` becomes a property. Deopt must call the "
            "descriptor."
        ),
        source='''class A:
    pass

a = A()
a.x = 1

def get(o):
    return o.x

for _ in range(1000):
    assert get(a) == 1

# Add a data descriptor with both __get__ and __set__ to the class.
# Data descriptors take priority over instance __dict__.
class Desc:
    def __get__(self, obj, owner):
        return 999
    def __set__(self, obj, value):
        pass  # no-op setter

A.x = Desc()
# Now a.x must return 999 (descriptor takes priority)
assert get(a) == 999
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         opt_state="deoptimized",
                         tags={"deopt", "attribute", "descriptor"}),
    ),
    T(
        name="deopt_during_method_call",
        category="deoptimization",
        description=(
            "JIT inlines a method call. Then a subclass overrides the "
            "method. Deopt must re-dispatch through the MRO."
        ),
        source='''\
class Base:
    def f(self): return "base"

class Derived(Base):
    pass

def call(o):
    return o.f()

d = Derived()
for _ in range(1000):
    assert call(d) == "base"

# Override in Derived
Derived.f = lambda self: "derived"
assert call(d) == "derived"
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         call_behavior="method", opt_state="deoptimized",
                         tags={"deopt", "method", "override"}),
    ),
    T(
        name="deopt_with_boxed_unboxed_mixed",
        category="deoptimization",
        description=(
            "JIT unboxes some locals as int64, others as float64. Deopt "
            "must rebox each according to its spec."
        ),
        source='''def work():
    a = 0       # int
    b = 0.0     # float
    c = 0       # int
    c_changed = False
    for i in range(1000):
        a += i
        b += i * 0.5
        if not c_changed:
            c += i
        if i == 500:
            # Trigger deopt by changing types
            a = a + 0.5    # a becomes float
            c = "string"   # c becomes str
            c_changed = True
    return a, b, c

a, b, c = work()
assert isinstance(a, float), f"a is {type(a)}"
assert isinstance(b, float), f"b is {type(b)}"
assert c == "string", f"c is {c!r}"

# Verify values: a accumulated ints 0..999, then +0.5 at i=500
expected_a = sum(range(1000)) + 0.5
assert a == expected_a, f"a={a}, expected={expected_a}"
expected_b = sum(i * 0.5 for i in range(1000))
assert abs(b - expected_b) < 1e-9
''',
        tags=TagSet.make("stress", type_stability="polymorphic",
                         control_flow="loop", opt_state="deoptimized",
                         tags={"deopt", "unbox", "mixed-types"}),
    ),
    T(
        name="deopt_preserves_exception_state",
        category="deoptimization",
        description=(
            "Exception is raised in optimized code. Deopt must preserve "
            "the exception object so it can be caught by a try/except "
            "in the caller."
        ),
        source='''def raiser(x):
    if x == 500:
        raise ValueError("mid")
    return x

def caller():
    total = 0
    for i in range(1000):
        try:
            total += raiser(i)
        except ValueError:
            total -= 1  # one ValueError caught at i=500
    return total

r = caller()
# When raiser(500) raises: total += raiser(500) doesn't execute, and
# total -= 1 runs. So we lose 500 from the sum and subtract 1.
expected = sum(range(500)) + sum(range(501, 1000)) - 1
assert r == expected, f"r={r}, expected={expected}"
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", opt_state="deoptimized",
                         tags={"deopt", "exception", "preserve"}),
    ),
    T(
        name="deopt_preserves_block_stack",
        category="deoptimization",
        description=(
            "Deopt happens inside a nested try/except/finally. The "
            "block stack must be reconstructed so the except/finally "
            "blocks run correctly."
        ),
        source='''\
def work():
    log = []
    try:
        for i in range(1000):
            if i == 500:
                # Trigger deopt by changing type
                x = "string"
            else:
                x = i
            log.append(x)
    except TypeError:
        log.append("type-error")
    finally:
        log.append("finally")
    return log

r = work()
assert len(r) == 1001
assert r[500] == "string"
assert r[-1] == "finally"
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         control_flow="loop", opt_state="deoptimized",
                         tags={"deopt", "block-stack", "finally"}),
    ),
    T(
        name="deopt_then_reopt_correct",
        category="deoptimization",
        description=(
            "Function deopts, runs in interpreter, then re-optimizes. "
            "The second optimization must produce correct results even "
            "though the type profile now includes the deopt-triggering "
            "type."
        ),
        source='''\
def work(values):
    acc = 0
    for v in values:
        acc += v
    return acc

# Warm up with ints
ints = list(range(100))
for _ in range(200):
    work(ints)

# Deopt with float
mixed = list(range(50)) + [0.5] * 50
assert work(mixed) == sum(mixed)

# Re-optimize with new profile (now includes float)
for _ in range(200):
    work(mixed)
assert work(mixed) == sum(mixed)

# And back to ints (deopt again)
assert work(ints) == sum(ints)
''',
        tags=TagSet.make("stress", type_stability="polymorphic",
                         control_flow="loop", opt_state="reheated",
                         tags={"deopt", "reopt", "type-profile"}),
    ),
    T(
        name="deopt_during_generator_yield",
        category="deoptimization",
        description=(
            "Generator yields from inside an optimized loop. Deopt "
            "happens at the yield point. The generator's suspended "
            "frame must be correctly reconstructed."
        ),
        source='''def gen(n):
    acc = 0
    for i in range(n):
        if i == 500:
            acc += 0.5  # type change -> deopt
        else:
            acc += i
        yield acc

results = list(gen(1000))
assert len(results) == 1000
assert results[0] == 0
assert results[499] == sum(range(500))
# At i=500: acc was sum(range(500)), then +0.5
assert results[500] == sum(range(500)) + 0.5
# At i=501: acc = sum(range(500)) + 0.5 + 501 (else branch)
assert results[501] == sum(range(500)) + 0.5 + 501
# Final: sum(range(500)) + 0.5 + sum(range(501, 1000))
expected_final = sum(range(500)) + 0.5 + sum(range(501, 1000))
assert results[-1] == expected_final, f"got {results[-1]}, expected {expected_final}"
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         control_flow="loop", call_behavior="generator",
                         opt_state="deoptimized", tags={"deopt", "generator", "yield"}),
    ),
    T(
        name="deopt_preserves_loop_counter",
        category="deoptimization",
        description=(
            "Deopt happens mid-loop. The loop counter `i` must have "
            "the correct value in the reconstructed interpreter frame."
        ),
        source='''\
def work():
    seen_i = []
    for i in range(1000):
        seen_i.append(i)
        if i == 500:
            x = "trigger"
        else:
            x = i
    return seen_i

seen = work()
assert seen[500] == 500
assert seen[0] == 0
assert seen[-1] == 999
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         control_flow="loop", opt_state="deoptimized",
                         tags={"deopt", "loop-counter"}),
    ),
    T(
        name="deopt_preserves_closure_cell",
        category="deoptimization",
        description=(
            "Deopt in a function with a captured closure variable. The "
            "closure cell must remain accessible after deopt."
        ),
        source='''\
def make():
    state = [0]
    def step(x):
        state[0] += x
        if x == 500:
            state[0] += 0.5  # deopt
        return state[0]
    return step

s = make()
results = []
for i in range(1000):
    results.append(s(i))

assert results[0] == 0
assert results[499] == sum(range(500))
assert results[500] == sum(range(501)) + 0.5
assert results[-1] == sum(range(1000)) + 0.5
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         control_flow="loop", call_behavior="closure",
                         opt_state="deoptimized", tags={"deopt", "closure", "cell"}),
    ),
    T(
        name="deopt_preserves_global_state",
        category="deoptimization",
        description=(
            "Deopt in a function that mutates a global. The global "
            "must reflect all mutations done before deopt."
        ),
        source='''\
G = [0]

def work():
    for i in range(1000):
        G[0] += i
        if i == 500:
            G[0] += 0.5  # deopt
    return G[0]

r = work()
assert r == sum(range(1000)) + 0.5
assert G[0] == r
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         control_flow="loop", opt_state="deoptimized",
                         tags={"deopt", "global", "state"}),
    ),
    T(
        name="deopt_during_chained_calls",
        category="deoptimization",
        description=(
            "Chained calls `a().b().c()`. Deopt happens at the second "
            "call. The first call's return value must be preserved."
        ),
        source='''class Chain:
    def __init__(self, v):
        self.v = v
    def a(self):
        return self
    def b(self):
        if self.v == 500:
            return "broken"  # returns str instead of Chain
        return self
    def c(self):
        return self.v

def work(n):
    results = []
    for i in range(n):
        obj = Chain(i)
        try:
            r = obj.a().b().c()
            results.append(r)
        except AttributeError:
            # "broken".c() raises AttributeError
            results.append("attr-error")
    return results

r = work(1000)
assert r[0] == 0
assert r[499] == 499
assert r[500] == "attr-error"
assert r[501] == 501
assert r[-1] == 999
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         call_behavior="method", opt_state="deoptimized",
                         tags={"deopt", "chained-call"}),
    ),
    T(
        name="deopt_with_keyword_arguments",
        category="deoptimization",
        description=(
            "Function called with keyword args. Deopt in the callee. "
            "The argument binding must be correctly reconstructed."
        ),
        source='''\
def f(a, b, c=10, d=20):
    if a == 500:
        return "trigger"
    return a + b + c + d

def caller():
    results = []
    for i in range(1000):
        results.append(f(i, i*2, c=i*3, d=i*4))
    return results

r = caller()
assert r[0] == 0 + 0 + 0 + 0
assert r[499] == 499 + 998 + 1497 + 1996
assert r[500] == "trigger"
assert r[501] == 501 + 1002 + 1503 + 2004
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         call_behavior="direct", opt_state="deoptimized",
                         tags={"deopt", "kwargs", "argument-binding"}),
    ),
    T(
        name="deopt_preserves_truthiness_speculation",
        category="deoptimization",
        description=(
            "JIT speculates `if x:` is testing an int (truthy if "
            "nonzero). Then x is a custom object with __bool__. Deopt "
            "must call __bool__."
        ),
        source='''class Weird:
    def __init__(self, v):
        self.v = v
    def __bool__(self):
        return self.v % 2 == 0

def check(x):
    if x:
        return "truthy"
    return "falsy"

# Warm up with ints
for i in range(1000):
    check(i)

# Now Weird objects
# Weird(0): 0 % 2 == 0 -> True -> "truthy"
assert check(Weird(0)) == "truthy"
# Weird(1): 1 % 2 == 0 -> False -> "falsy"
assert check(Weird(1)) == "falsy"
# Weird(2): 2 % 2 == 0 -> True -> "truthy"
assert check(Weird(2)) == "truthy"

# int 0 -> falsy, int 1 -> truthy
assert check(0) == "falsy"
assert check(1) == "truthy"
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         control_flow="if_else", opt_state="deoptimized",
                         tags={"deopt", "truthiness", "bool"}),
    ),
    T(
        name="deopt_preserves_iteration_state",
        category="deoptimization",
        description=(
            "Loop iterating a list. Deopt happens. The list iterator's "
            "internal index must be preserved."
        ),
        source='''\
def work(lst):
    seen = []
    for i, x in enumerate(lst):
        seen.append(x)
        if i == 500:
            y = "trigger"
    return seen

lst = list(range(1000))
seen = work(lst)
assert seen == lst
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         control_flow="loop", opt_state="deoptimized",
                         tags={"deopt", "iterator", "index"}),
    ),
    T(
        name="deopt_then_inline_cache_invalidation",
        category="deoptimization",
        description=(
            "Deopt and IC invalidation happen close together. The "
            "reconstructed frame must use the new IC, not the old "
            "stale cache."
        ),
        source='''\
class A:
    x = 1
class B(A):
    pass

def get(o):
    return o.x

b = B()
for _ in range(1000):
    assert get(b) == 1

# Add x to B (invalidates IC)
B.x = 99
assert get(b) == 99

# Trigger deopt in a different code path
def work():
    acc = 0
    for i in range(1000):
        if i == 500:
            acc += 0.5
        else:
            acc += i
    return acc

assert work() == sum(range(500)) + 0.5 + sum(range(501, 1000))
''',
        tags=TagSet.make("stress", type_stability="polymorphic",
                         opt_state="deoptimized",
                         tags={"deopt", "IC", "invalidation"}),
    ),
    T(
        name="deopt_preserves_recursion_depth",
        category="deoptimization",
        description=(
            "Recursive function. Deopt happens at depth N. The "
            "interpreter must continue with the correct recursion "
            "depth and locals at each level."
        ),
        source='''import sys

# Raise the limit so sum_to(1000) doesn't hit it
sys.setrecursionlimit(10000)

def sum_to(n):
    if n <= 0:
        return 0
    return n + sum_to(n - 1)

assert sum_to(100) == 5050
assert sum_to(500) == 125250
assert sum_to(1000) == 500500

# Edge cases
assert sum_to(0) == 0
assert sum_to(1) == 1
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="recursion", call_behavior="recursive",
                         opt_state="deoptimized", tags={"deopt", "recursion", "depth"}),
    ),
    T(
        name="deopt_preserves_walrus_binding",
        category="deoptimization",
        description=(
            "Walrus operator `:=` binds a variable in an enclosing scope. "
            "Deopt must preserve the binding."
        ),
        source='''def work():
    results = []
    for i in range(1000):
        if (n := i * 2) > 500:
            results.append(n)
        if i == 500:
            x = "trigger"
    return results

r = work()
# n = i * 2; n > 500 means i > 250, so i in range(251, 1000)
assert len(r) == 749
assert r[0] == 502    # i=251 -> n=502
assert r[-1] == 1998  # i=999 -> n=1998
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         control_flow="loop", opt_state="deoptimized",
                         tags={"deopt", "walrus", "binding"}),
    ),
    T(
        name="deopt_preserves_starred_assignment",
        category="deoptimization",
        description=(
            "Starred unpacking `a, *b, c = ...`. Deopt must preserve "
            "the list `b`."
        ),
        source='''\
def work():
    results = []
    for i in range(1000):
        seq = list(range(i, i + 10))
        a, *b, c = seq
        results.append((a, b, c))
        if i == 500:
            x = "trigger"
    return results

r = work()
assert r[0] == (0, [1, 2, 3, 4, 5, 6, 7, 8], 9)
assert r[500] == (500, [501, 502, 503, 504, 505, 506, 507, 508], 509)
assert r[-1] == (999, [1000, 1001, 1002, 1003, 1004, 1005, 1006, 1007], 1008)
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         control_flow="loop", opt_state="deoptimized",
                         tags={"deopt", "starred", "unpack"}),
    ),
    T(
        name="deopt_preserves_assert_state",
        category="deoptimization",
        description=(
            "Assertion inside a hot loop. Deopt must preserve the "
            "assertion's failure behavior."
        ),
        source='''\
def work():
    for i in range(1000):
        assert i >= 0
        if i == 500:
            x = "trigger"
    return "ok"

assert work() == "ok"
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         control_flow="loop", opt_state="deoptimized",
                         tags={"deopt", "assert"}),
    ),
]
