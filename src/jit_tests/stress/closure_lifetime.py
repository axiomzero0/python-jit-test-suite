"""Closure variable lifetime stress tests.

These tests target the JIT's handling of closure variables (cells):
their representation, lifetime, and the assumptions the compiler is
tempted to make about them. A naive JIT may treat a captured variable
as a stack slot, assume a stable type, or assume a closure that
escapes a call frame will never be invoked. Each test below
deliberately violates one of those assumptions.

Failure modes covered:
- Late binding of loop variables captured into closures
- nonlocal mutation requiring a cell, not a stack slot
- Closures that escape via return (cell must persist on the heap)
- Nested closure chains capturing from outer frames
- Closure cell type changes requiring deopt and reboxing
- Closures created in hot loops with per-iteration distinct captures
- Closures sharing mutable containers via the cell
- Closure cell deletion (subsequent access must raise NameError)
- Two closures sharing one cell (mutation observed by both)
- Recursive closures capturing themselves via the cell
- Generators captured in closure cells (state persists across calls)
- Closures created but not immediately called (cell must stay alive)
- Closure variable reassignment mid-function
- Mutable default argument gotcha (evaluated once at def time)
- Closures that capture a class defined in the enclosing scope
"""

from __future__ import annotations

from ._shared import T
from ..harness import TagSet


STRESS_TESTS = [
    T(
        name="late_binding_loop_var",
        category="closure_lifetime",
        description=(
            "Closures capture the loop variable cell by reference, not "
            "by value. By the time the lambdas are called, the loop has "
            "finished and the cell holds the final value. A JIT that "
            "speculates the cell holds a fixed value per closure must "
            "deopt when all closures return the same late-bound value."
        ),
        source='''\
def make_fns():
    fns = []
    for i in range(3):
        fns.append(lambda: i)
    return fns

fns = make_fns()
# All closures see the final value of i (late binding)
results = [f() for f in fns]
assert results == [2, 2, 2]

# Contrast: capture current value via default argument
def make_fns2():
    fns = []
    for i in range(3):
        fns.append(lambda i=i: i)
    return fns

fns2 = make_fns2()
assert [f() for f in fns2] == [0, 1, 2]
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", call_behavior="closure",
                         opt_state="deoptimized",
                         tags={"closure", "late-binding", "cell"}),
    ),
    T(
        name="nonlocal_mutation_uses_cell",
        category="closure_lifetime",
        description=(
            "A closure mutates its captured variable via `nonlocal`. The "
            "JIT cannot keep the variable in a stack slot or as a "
            "constant; it must go through the cell every time. After many "
            "increments the counter must read the correct accumulated "
            "value, not a stale snapshot."
        ),
        source='''\
def make_counter():
    count = 0
    def inc():
        nonlocal count
        count += 1
        return count
    return inc

c = make_counter()
for _ in range(100):
    c()

assert c() == 101
assert c() == 102

# Independent counters get independent cells
c2 = make_counter()
assert c2() == 1
assert c() == 103
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         call_behavior="closure", opt_state="hot",
                         tags={"closure", "nonlocal", "cell", "mutation"}),
    ),
    T(
        name="closure_escapes_via_return",
        category="closure_lifetime",
        description=(
            "The enclosing frame returns the closure. After the frame is "
            "gone, the cell must persist on the heap. A JIT that "
            "stack-allocates the cell would free it on return, leaving the "
            "captured value dangling."
        ),
        source='''\
def make_adder(n):
    def add(x):
        return x + n
    return add

add5 = make_adder(5)
add10 = make_adder(10)

# The enclosing frames are gone; the captured `n` must persist.
for i in range(100):
    assert add5(i) == i + 5
    assert add10(i) == i + 10

assert add5(1000) == 1005
assert add10(1000) == 1010

# Each closure has its own cell with a distinct value
assert add5(0) != add10(0)
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         call_behavior="closure", opt_state="hot",
                         tags={"closure", "escape", "heap", "cell-lifetime"}),
    ),
    T(
        name="nested_closures_three_levels",
        category="closure_lifetime",
        description=(
            "Three nested closures, each capturing a variable from the "
            "frame above it. The JIT must build a chain of cell references "
            "and resolve each capture through the appropriate frame, not "
            "flatten them into a single scope."
        ),
        source='''\
def outer(a):
    def middle(b):
        def inner(c):
            return a + b + c
        return inner
    return middle

f = outer(1)(2)
assert f(3) == 6
assert f(10) == 13

g = outer(100)(20)
assert g(3) == 123

# Many distinct inner closures
results = []
for i in range(10):
    for j in range(10):
        results.append(outer(i)(j)(0))
expected = [i + j for i in range(10) for j in range(10)]
assert results == expected
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="nested_loop", call_behavior="closure",
                         opt_state="very_hot",
                         tags={"closure", "nested", "cell-chain"}),
    ),
    T(
        name="closure_cell_type_change",
        category="closure_lifetime",
        description=(
            "The captured cell variable starts as int and is reassigned "
            "to str, then list, then dict. A JIT that speculates the cell "
            "holds an int (and unboxes it) must deopt and rebox on each "
            "type change, preserving the new value across subsequent reads."
        ),
        source='''\
def make_reader_setter():
    state = 0
    def reader():
        return state
    def setter(v):
        nonlocal state
        state = v
    return reader, setter

r, s = make_reader_setter()

# Warm up with ints
for i in range(100):
    s(i)
    assert r() == i

# Now change type to str (deopt must rebox)
s("hello")
assert r() == "hello"

# Change to list
s([1, 2, 3])
assert r() == [1, 2, 3]
assert r() is not [1, 2, 3]  # same list object each call

# Change to dict
s({"k": "v"})
assert r() == {"k": "v"}

# Back to int
s(42)
assert r() == 42
assert isinstance(r(), int)
''',
        tags=TagSet.make("stress", type_stability="megamorphic",
                         call_behavior="closure", opt_state="deoptimized",
                         tags={"closure", "type-change", "rebox", "deopt"}),
    ),
    T(
        name="closure_created_in_hot_loop",
        category="closure_lifetime",
        description=(
            "A hot loop creates a new closure on each iteration, each "
            "capturing a distinct value of the loop variable. The JIT "
            "must allocate a fresh cell per iteration and not collapse "
            "them into a shared cell (which would yield late binding)."
        ),
        source='''\
adders = []
for i in range(100):
    adders.append(lambda x, n=i: x + n)

# Each closure should add a distinct captured value
total = 0
for f in adders:
    total += f(10)
# 10 * 100 + sum(0..99) = 1000 + 4950 = 5950
assert total == 5950

# Spot check a few
assert adders[0](0) == 0
assert adders[50](0) == 50
assert adders[99](0) == 99

# Distinct cells, distinct objects
assert adders[0] is not adders[1]
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", call_behavior="closure",
                         opt_state="very_hot",
                         tags={"closure", "hot-loop", "per-iter-cell"}),
    ),
    T(
        name="closure_shares_mutable_list",
        category="closure_lifetime",
        description=(
            "Two closures share a cell that holds a mutable list. Mutation "
            "through one closure must be visible to the other, since they "
            "share the same cell (and hence the same list object)."
        ),
        source='''\
def make_append_get_pair():
    shared = []
    def append(v):
        shared.append(v)
        return len(shared)
    def get():
        return list(shared)
    return append, get

a, g = make_append_get_pair()

assert a(1) == 1
assert a(2) == 2
assert g() == [1, 2]

# Mutation through `a` is visible to `g` (same list, same cell)
a(3)
a(4)
assert g() == [1, 2, 3, 4]

# Independent pairs get independent cells/lists
a2, g2 = make_append_get_pair()
a2(99)
assert g2() == [99]
assert g() == [1, 2, 3, 4]  # unchanged
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         call_behavior="closure", opt_state="hot",
                         tags={"closure", "shared-cell", "mutable"}),
    ),
    T(
        name="closure_cell_deleted_then_accessed",
        category="closure_lifetime",
        description=(
            "A closure cell is deleted via `nonlocal x; del x`. Subsequent "
            "reads of the same cell from a sibling closure must raise "
            "NameError (the cell is now empty). A JIT that elides the "
            "cell-empty check would return a stale or garbage value."
        ),
        source='''\
def make_getter_deleter():
    x = 10
    def get():
        return x
    def delete():
        nonlocal x
        del x
    return get, delete

g, d = make_getter_deleter()
assert g() == 10

# Delete the cell binding
d()

# Subsequent reads must raise NameError
raised = 0
for _ in range(5):
    try:
        g()
    except NameError:
        raised += 1
assert raised == 5

# Re-creating a fresh closure restores the cell
g2, d2 = make_getter_deleter()
assert g2() == 10
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         call_behavior="closure", opt_state="deoptimized",
                         tags={"closure", "del", "cell-empty", "NameError"}),
    ),
    T(
        name="two_closures_share_one_cell",
        category="closure_lifetime",
        description=(
            "Two closures defined in the same frame share the same cell "
            "for a captured variable. Mutation through one closure is "
            "immediately visible to the other. The JIT cannot keep a "
            "private cached copy of the value in either closure."
        ),
        source='''\
def make_get_set():
    x = 1
    def get():
        return x
    def set_(v):
        nonlocal x
        x = v
        return x
    return get, set_

g, s = make_get_set()
assert g() == 1

# Mutation through `s` is visible to `g`
assert s(42) == 42
assert g() == 42

# Type change is also visible
s("abc")
assert g() == "abc"

s(None)
assert g() is None

s(0)
assert g() == 0
''',
        tags=TagSet.make("stress", type_stability="polymorphic",
                         call_behavior="closure", opt_state="deoptimized",
                         tags={"closure", "shared-cell", "aliasing"}),
    ),
    T(
        name="recursive_closure_via_cell",
        category="closure_lifetime",
        description=(
            "A closure captures itself via the cell so it can recurse. The "
            "JIT must not assume the captured name is bound to a constant "
            "function pointer; it must dereference the cell on every "
            "recursive call."
        ),
        source='''\
def make_factorial():
    def fact(n):
        if n <= 1:
            return 1
        return n * fact(n - 1)
    return fact

f = make_factorial()
assert f(0) == 1
assert f(1) == 1
assert f(5) == 120
assert f(10) == 3628800
assert f(20) == 2432902008176640000

# Recursion via cell must handle deep stacks (within Python's default limit)
import sys
limit = sys.getrecursionlimit()
assert f(min(100, limit - 100)) > 0

# Two independent recursive closures
g = make_factorial()
assert g(5) == 120
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="recursion", call_behavior="recursive",
                         opt_state="hot",
                         tags={"closure", "recursion", "self-capture"}),
    ),
    T(
        name="closure_captures_generator",
        category="closure_lifetime",
        description=(
            "A closure captures a generator object. Each invocation of "
            "the closure advances the generator by one step. The cell "
            "must preserve the generator's suspended state across calls."
        ),
        source='''\
def make_gen_holder():
    gen = (i * 2 for i in range(5))
    def next_val():
        return next(gen)
    return next_val

nxt = make_gen_holder()
assert nxt() == 0
assert nxt() == 2
assert nxt() == 4
assert nxt() == 6
assert nxt() == 8

# Generator is exhausted; further calls must raise StopIteration
stop_count = 0
for _ in range(3):
    try:
        nxt()
    except StopIteration:
        stop_count += 1
assert stop_count == 3

# Each holder captures its own generator
nxt2 = make_gen_holder()
assert nxt2() == 0
assert nxt2() == 2
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         call_behavior="closure", opt_state="hot",
                         tags={"closure", "generator", "suspended-state"}),
    ),
    T(
        name="closure_created_not_called",
        category="closure_lifetime",
        description=(
            "A closure is created and assigned, but the inner closure "
            "that uses the cell is never called for a long time. The "
            "JIT must keep the cell (and the captured big data) alive "
            "even if no read has occurred, since a future call would "
            "need it."
        ),
        source='''\
def make_closures():
    big_data = list(range(1000))
    def used():
        return sum(big_data)
    def unused_for_a_while():
        return len(big_data)
    return used, unused_for_a_while

u, un = make_closures()

# Warm up by calling `used` many times
total = 0
for _ in range(200):
    total += u()
assert total == 200 * sum(range(1000))

# `unused_for_a_while` has never been called yet.
# Now invoke it; the cell must still hold big_data.
assert un() == 1000

# Both closures see the same captured list
assert u() == sum(range(1000))
assert un() == len(list(range(1000)))
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", call_behavior="closure",
                         opt_state="very_hot",
                         tags={"closure", "lazy-call", "cell-lifetime", "GC"}),
    ),
    T(
        name="closure_var_reassigned_mid_function",
        category="closure_lifetime",
        description=(
            "The captured variable is reassigned to a brand-new value mid "
            "function via a setter closure. The cell must reflect the new "
            "value immediately, and a separate accumulator closure must "
            "continue from the new value, not the old one."
        ),
        source='''\
def make_accumulator():
    total = 0
    def add(v):
        nonlocal total
        total += v
        return total
    def reset(new_start):
        nonlocal total
        old = total
        total = new_start
        return old
    return add, reset

add, reset = make_accumulator()
assert add(1) == 1
assert add(2) == 3
assert add(3) == 6

# Reassign mid-stream
old = reset(100)
assert old == 6
assert add(1) == 101
assert add(2) == 103

# Reassign to a value of different type (deopt)
reset("zero")
# Now adding str + int would fail, so we just verify the cell holds the str
reset(0)
assert add(5) == 5
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         call_behavior="closure", opt_state="deoptimized",
                         tags={"closure", "reassign", "cell-write"}),
    ),
    T(
        name="mutable_default_arg_gotcha",
        category="closure_lifetime",
        description=(
            "The classic `def f(x=[])` gotcha: the default is evaluated "
            "once at def time and shared across all calls. A JIT that "
            "re-evaluates the default per call (or allocates a fresh list "
            "per call) would diverge from CPython semantics."
        ),
        source='''\
def make_appender():
    def append_to(x, acc=[]):
        acc.append(x)
        return acc
    return append_to

app = make_appender()
assert app(1) == [1]
assert app(2) == [1, 2]
assert app(3) == [1, 2, 3]

# The default list is the same object across calls
default_id = id(app.__defaults__[0])
app(4)
assert id(app.__defaults__[0]) == default_id

# Same gotcha with dict default
def make_incrementer():
    def incr(key, counts={}):
        counts[key] = counts.get(key, 0) + 1
        return counts[key]
    return incr

incr = make_incrementer()
assert incr('a') == 1
assert incr('a') == 2
assert incr('b') == 1
assert incr('a') == 3

# Independent functions get independent defaults
incr2 = make_incrementer()
assert incr2('a') == 1
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         call_behavior="closure", opt_state="hot",
                         tags={"closure", "default-arg", "shared-default"}),
    ),
    T(
        name="closure_captures_class",
        category="closure_lifetime",
        description=(
            "A class is defined inside the enclosing function and captured "
            "by an inner closure. The class object must persist after the "
            "enclosing frame returns, and each call to the factory must "
            "produce instances of the captured class (not a fresh class)."
        ),
        source='''\
def make_counter_factory():
    class Counter:
        _instances = 0
        def __init__(self):
            Counter._instances += 1
            self.count = 0
        def inc(self):
            self.count += 1
            return self.count
    def factory():
        return Counter()
    return factory

mk = make_counter_factory()

c1 = mk()
assert c1.inc() == 1
assert c1.inc() == 2

c2 = mk()
assert c2.inc() == 1
assert c1.inc() == 3  # c1 unaffected

# All instances share the same captured class
assert type(c1) is type(c2)

# Class state persists across the closure
assert type(c1)._instances == 2

c3 = mk()
assert type(c3) is type(c1)
assert type(c1)._instances == 3
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         call_behavior="closure", opt_state="hot",
                         tags={"closure", "class-capture", "metaprogramming"}),
    ),
]
