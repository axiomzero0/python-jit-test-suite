"""OSR (On-Stack Replacement) stress tests.

OSR is the mechanism by which a JIT replaces a running interpreter
frame with a compiled frame (OSR entry) or vice versa (OSR exit /
deoptimization). This is one of the hardest things to get right in a
JIT because the compiled frame must reconstruct the exact state of
the interpreter frame, including:

- All local variables (including unboxed ones)
- The current loop iteration counter
- Live exception state
- Pending finally blocks
- Generator/coroutine state

Each test below exercises a specific OSR edge case.
"""

from __future__ import annotations

from ._shared import T
from ..harness import TagSet


STRESS_TESTS = [
    T(
        name="osr_entry_mid_loop_with_locals",
        category="osr",
        description=(
            "OSR entry happens after the loop has been running for a "
            "while. The compiled frame must reconstruct all live locals "
            "(`acc`, `i`, `tmp`, `flag`)."
        ),
        source='''\
def work(n):
    acc = 0
    flag = False
    for i in range(n):
        tmp = i * 2
        acc += tmp
        if i == n // 2:
            flag = True
    return acc, flag, tmp

a, f, t = work(1000)
assert a == sum(i * 2 for i in range(1000))
assert f is True
assert t == 999 * 2
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", opt_state="hot",
                         tags={"OSR", "entry", "locals"}),
    ),
    T(
        name="osr_exit_during_arithmetic",
        category="osr",
        description=(
            "Hot loop runs optimized for 1000 iterations. On iteration "
            "1001, a type speculation fails (int -> float). The OSR exit "
            "must reconstruct the loop state with the correct float value "
            "of `acc`."
        ),
        source='''\
def accumulate(values):
    acc = 0
    for v in values:
        acc += v  # speculation: int+int
    return acc

# All ints for warmup
ints = list(range(1000))
assert accumulate(ints) == sum(ints)

# Now mix in a float — deopt on iteration 1001
mixed = list(range(1000)) + [0.5, 0.5]
r = accumulate(mixed)
assert r == sum(mixed)
assert isinstance(r, float)
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         control_flow="loop", opt_state="deoptimized",
                         tags={"OSR", "exit", "type-speculation"}),
    ),
    T(
        name="osr_entry_with_closures",
        category="osr",
        description=(
            "OSR entry into a function that has captured closure variables. "
            "The compiled frame must correctly bind the closure cells."
        ),
        source='''\
def make_counter(start):
    count = [start]
    def step():
        count[0] += 1
        return count[0]
    return step

c = make_counter(0)
results = []
for _ in range(10000):
    results.append(c())

assert results[0] == 1
assert results[-1] == 10000
assert len(set(results)) == 10000  # all unique
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", call_behavior="closure",
                         opt_state="hot", tags={"OSR", "closure", "cell"}),
    ),
    T(
        name="osr_exit_with_active_exception",
        category="osr",
        description=(
            "Hot loop raises an exception on iteration 500. The OSR exit "
            "must propagate the exception correctly through any compiled "
            "frame, unwinding finally blocks as it goes."
        ),
        source='''\
def work():
    try:
        for i in range(1000):
            if i == 500:
                raise ValueError("mid-loop")
        return "no-exception"
    except ValueError as e:
        return f"caught at i={i}: {e}"

r = work()
assert "caught at i=500" in r
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", opt_state="deoptimized",
                         tags={"OSR", "exit", "exception", "finally"}),
    ),
    T(
        name="osr_entry_in_nested_loop",
        category="osr",
        description=(
            "OSR entry into the *inner* loop of a nested loop structure. "
            "The compiled frame must know which loop is being entered "
            "and reconstruct both loop counters."
        ),
        source='''\
def nested(n):
    total = 0
    for i in range(n):
        for j in range(n):
            total += i * j
    return total

assert nested(100) == sum(i * j for i in range(100) for j in range(100))
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="nested_loop", opt_state="hot",
                         tags={"OSR", "nested-loop"}),
    ),
    T(
        name="osr_exit_with_finally",
        category="osr",
        description=(
            "Hot loop inside a try/finally. OSR exit (deopt) happens "
            "inside the loop. The finally block must execute with the "
            "correct reconstructed state."
        ),
        source='''\
def work():
    finally_ran = [False]
    try:
        acc = 0
        for i in range(1000):
            acc += i
            if i == 500:
                # Simulate a deopt trigger (different type)
                acc += 0.5
    finally:
        finally_ran[0] = True
    return acc, finally_ran[0]

acc, ran = work()
assert ran is True
assert acc == sum(range(501)) + 0.5 + sum(range(501, 1000))
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         control_flow="loop", opt_state="deoptimized",
                         tags={"OSR", "exit", "finally", "unwind"}),
    ),
    T(
        name="osr_exit_to_generator",
        category="osr",
        description=(
            "Hot loop inside a generator. OSR exit happens while the "
            "generator is suspended at a yield. The generator's frame "
            "must be correctly reconstructed when resumed."
        ),
        source='''\
def gen(n):
    acc = 0
    for i in range(n):
        acc += i
        if i == 500:
            acc += 0.5  # type change -> deopt
        yield acc

g = gen(1000)
results = list(g)
assert len(results) == 1000
assert results[0] == 0
assert results[499] == sum(range(500))
assert results[500] == sum(range(501)) + 0.5
assert results[-1] == sum(range(1000)) + 0.5
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         control_flow="loop", call_behavior="generator",
                         opt_state="deoptimized", tags={"OSR", "generator", "yield"}),
    ),
    T(
        name="osr_entry_at_loop_back_edge",
        category="osr",
        description=(
            "OSR entry at the loop back-edge (the typical entry point). "
            "This verifies that the JIT can replace the interpreter "
            "frame at exactly the right instruction (the back-edge jump)."
        ),
        source='''\
def work(n):
    s = 0
    for i in range(n):
        s += i
    return s

# Large enough to trigger OSR
assert work(100_000) == sum(range(100_000))
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", opt_state="very_hot",
                         tags={"OSR", "back-edge"}),
    ),
    T(
        name="osr_exit_during_call",
        category="osr",
        description=(
            "OSR exit happens during a function call (the callee returns "
            "a value of an unexpected type). The compiled frame must "
            "deopt with the correct return value already on the stack."
        ),
        source='''\
def callee(x):
    if x == 500:
        return "unexpected"
    return x * 2

def caller(n):
    acc = 0
    for i in range(n):
        r = callee(i)
        acc += r if isinstance(r, int) else 0
    return acc

assert caller(1000) == sum(i * 2 for i in range(500)) + sum(i * 2 for i in range(501, 1000))
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         control_flow="loop", call_behavior="direct",
                         opt_state="deoptimized", tags={"OSR", "call", "exit"}),
    ),
    T(
        name="osr_with_many_live_variables",
        category="osr",
        description=(
            "OSR with 10+ live variables. Stress-tests the register "
            "spill/reload logic during state reconstruction."
        ),
        source='''\
def work(n):
    a = b = c = d = e = f = g = h = i = j = 0
    for x in range(n):
        a += x
        b += x * 2
        c += x * 3
        d += x * 4
        e += x * 5
        f += x * 6
        g += x * 7
        h += x * 8
        i += x * 9
        j += x * 10
    return (a, b, c, d, e, f, g, h, i, j)

result = work(1000)
expected = (sum(x * k for x in range(1000)) for k in range(1, 11))
assert result == tuple(expected)
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", opt_state="very_hot",
                         tags={"OSR", "registers", "live-variables"}),
    ),
    T(
        name="osr_exit_preserves_iterator_state",
        category="osr",
        description=(
            "Hot loop iterating a list. OSR exit (deopt) happens "
            "mid-iteration. The iterator's internal position must be "
            "preserved so the interpreter continues from the right place."
        ),
        source='''\
def work(items):
    total = 0
    for i, x in enumerate(items):
        total += x
        if i == 500:
            total += 0.5  # deopt trigger
    return total

items = list(range(1000))
r = work(items)
expected = sum(items[:501]) + 0.5 + sum(items[501:])
assert r == expected
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         control_flow="loop", opt_state="deoptimized",
                         tags={"OSR", "iterator", "position"}),
    ),
    T(
        name="osr_entry_into_recursive_function",
        category="osr",
        description=(
            "OSR into a recursive function. The compiled frame must "
            "preserve the call chain so the recursion can return "
            "correctly."
        ),
        source='''\
def fib(n):
    if n <= 1:
        return n
    return fib(n - 1) + fib(n - 2)

# Large enough to trigger OSR in the top-level call
assert fib(30) == 832040
assert fib(35) == 9227465
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="recursion", call_behavior="recursive",
                         opt_state="hot", tags={"OSR", "recursion"}),
    ),
    T(
        name="osr_exit_with_pending_finally_chain",
        category="osr",
        description=(
            "Three nested try/finally blocks. OSR exit happens in the "
            "innermost loop. All three finally blocks must execute in "
            "the correct order during unwind."
        ),
        source='''\
order = []

def work():
    try:
        try:
            try:
                for i in range(1000):
                    if i == 500:
                        raise RuntimeError("deopt trigger")
            finally:
                order.append("inner")
        finally:
            order.append("middle")
    finally:
        order.append("outer")

try:
    work()
except RuntimeError:
    pass

# All three finally blocks must execute in order, even though the
# exception propagates out of work(). The "outer" append runs in the
# finally, then the RuntimeError escapes.
assert order == ["inner", "middle", "outer"]
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="nested_loop", opt_state="deoptimized",
                         tags={"OSR", "finally", "unwind", "exception"}),
    ),
    T(
        name="osr_reentry_after_deopt",
        category="osr",
        description=(
            "Function deopts mid-loop. After deopt, the interpreter "
            "runs for a while, then the JIT re-optimizes and OSRs "
            "back in. The second optimization must be correct."
        ),
        source='''\
def work(values):
    acc = 0
    for v in values:
        acc += v
    return acc

# Warm up
ints = list(range(1000))
for _ in range(100):
    work(ints)

# Deopt
mixed = list(range(500)) + [0.5] * 500
assert work(mixed) == sum(mixed)

# Re-optimize
ints = list(range(2000))
for _ in range(100):
    work(ints)
assert work(ints) == sum(ints)
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         control_flow="loop", opt_state="reheated",
                         tags={"OSR", "reentry", "reopt"}),
    ),
    T(
        name="osr_with_comprehension",
        category="osr",
        description=(
            "OSR into a list comprehension's implicit loop. The "
            "comprehension's hidden state (the result list, the "
            "iterator, the condition) must all be reconstructed."
        ),
        source='''\
def work(n):
    return [i * i for i in range(n) if i % 2 == 0]

r = work(10000)
assert len(r) == 5000
assert r[0] == 0
assert r[-1] == 9998 ** 2
assert r[2500] == 5000 ** 2
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", opt_state="very_hot",
                         tags={"OSR", "comprehension"}),
    ),
]
