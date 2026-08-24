"""Aliasing and memory model stress tests.

A JIT compiler that performs escape analysis, scalar replacement, or
loop-invariant code motion must respect Python's reference semantics: two
variables (or two container slots, or a closure cell and a local) can
refer to the *same* underlying object, and a mutation through one
reference must be visible through every other alias.

Each test below constructs a deliberate aliasing scenario that is easy
to get wrong if the JIT:

  * assumes two list references never alias and hoists a length/element
    read out of a loop;
  * caches a container's hash, size, or element pointer across a call
    that may mutate the container;
  * specializes on the (immutable) shape of a tuple and forgets that
    the tuple's *contents* may be mutable;
  * reuses interned/cached object identities as a proxy for value
    equality;
  * inlines a function and assumes its argument list is private to the
    compiled frame.

The tests are all well-defined under CPython and assert the observable
behavior. A correct JIT must produce the same result.
"""

from __future__ import annotations

from ._shared import T
from ..harness import TagSet


STRESS_TESTS = [
    # ------------------------------------------------------------------
    # 1. Direct aliasing of the same list.
    # ------------------------------------------------------------------
    T(
        name="alias_same_list_mutation_visible",
        category="aliasing",
        description=(
            "Two names bound to the same list object: a mutation through "
            "one name must be visible through the other. A JIT that "
            "speculates `a` and `b` are distinct objects (e.g. because "
            "they have separate SSA names) would mis-observe `a` after "
            "the append."
        ),
        source='''\
a = [1, 2, 3]
b = a
b.append(4)
assert a == [1, 2, 3, 4]
assert b == [1, 2, 3, 4]
assert a is b
b.extend([5, 6])
assert a == [1, 2, 3, 4, 5, 6]
b[0] = 99
assert a[0] == 99
assert a == [99, 2, 3, 4, 5, 6]
''',
        tags=TagSet.make("containers", type_stability="monomorphic",
                         control_flow="straight_line", opt_state="deoptimized",
                         tags={"stress", "aliasing", "container", "list"}),
    ),
    # ------------------------------------------------------------------
    # 2. Nested aliasing: a[0] is b.
    # ------------------------------------------------------------------
    T(
        name="nested_list_slot_aliased",
        category="aliasing",
        description=(
            "An outer list holds a reference to an inner list. Mutating "
            "the inner list (through its alias `b`) must change what the "
            "outer list's slot reports. A JIT that scalar-replaces the "
            "outer list's elements into unboxed locals would lose this."
        ),
        source='''\
b = [10, 20]
a = [b, 99]
b.append(30)
assert a[0] == [10, 20, 30]
assert a[0] is b
b[0] = 999
assert a[0][0] == 999
a[0].append(40)
assert b == [999, 20, 30, 40]
''',
        tags=TagSet.make("containers", type_stability="monomorphic",
                         control_flow="straight_line", opt_state="deoptimized",
                         tags={"stress", "aliasing", "container", "list", "nested"}),
    ),
    # ------------------------------------------------------------------
    # 3. Cyclic aliasing: a and b reference each other.
    # ------------------------------------------------------------------
    T(
        name="cyclic_aliasing_self_reference",
        category="aliasing",
        description=(
            "Construct two containers that reference each other (a cycle). "
            "The JIT must not assume acyclic reference graphs and must not "
            "loop forever when traversing. Equality and repr must terminate."
        ),
        source='''\
a = []
b = [a]
a.append(b)
# a == [[...]] and b == [[[...]]] -- cyclic
assert a[0] is b
assert b[0] is a
assert a[0][0] is a
# Append through one alias, observe through the other
a.append("tag")
assert b[0][1] == "tag"
assert len(b[0]) == 2
# repr is well-defined (recursive)
s = repr(a)
assert "..." in s
''',
        tags=TagSet.make("containers", type_stability="monomorphic",
                         control_flow="straight_line", opt_state="deoptimized",
                         tags={"stress", "aliasing", "container", "cycle", "list"}),
    ),
    # ------------------------------------------------------------------
    # 4. Dict aliasing through a shared mutable value object.
    # ------------------------------------------------------------------
    T(
        name="dict_shared_mutable_value_object",
        category="aliasing",
        description=(
            "Two dicts store the *same* mutable value object under "
            "different keys. Mutating that shared value (in place) must "
            "be visible through both dicts. A JIT that snapshots dict "
            "values into locals and reuses them across calls would miss "
            "the in-place mutation."
        ),
        source='''\
shared = [1, 2]
d1 = {"a": shared}
d2 = {"b": shared}
assert d1["a"] is d2["b"]
shared.append(3)
assert d1["a"] == [1, 2, 3]
assert d2["b"] == [1, 2, 3]
# Mutate through the dict slot
d1["a"].append(4)
assert d2["b"] == [1, 2, 3, 4]
assert shared == [1, 2, 3, 4]
''',
        tags=TagSet.make("containers", type_stability="monomorphic",
                         control_flow="straight_line", opt_state="deoptimized",
                         tags={"stress", "aliasing", "container", "dict", "value"}),
    ),
    # ------------------------------------------------------------------
    # 5. Mutation during list iteration (append path).
    # ------------------------------------------------------------------
    T(
        name="mutation_during_list_iteration_append",
        category="aliasing",
        description=(
            "Appending to a list while iterating over it with a for-loop "
            "is *well-defined* for lists in CPython (the iterator indexes "
            "into the list and re-reads its length each step, so the loop "
            "will visit newly-appended items until terminated explicitly). "
            "A JIT that snapshots `len(xs)` before the loop would either "
            "stop early or skip items."
        ),
        source='''\
xs = [0]
seen = []
for x in xs:
    seen.append(x)
    if x < 5:
        xs.append(x + 1)
# Each iteration observes the freshly appended element.
assert seen == [0, 1, 2, 3, 4, 5]
assert xs == [0, 1, 2, 3, 4, 5]
''',
        tags=TagSet.make("containers", type_stability="monomorphic",
                         control_flow="loop", opt_state="hot",
                         tags={"stress", "aliasing", "container", "list",
                               "mutation-during-iter"}),
    ),
    # ------------------------------------------------------------------
    # 6. Mutation during dict iteration (must raise).
    # ------------------------------------------------------------------
    T(
        name="mutation_during_dict_iteration_raises",
        category="aliasing",
        description=(
            "Adding or removing keys during dict iteration must raise "
            "RuntimeError (CPython sets a `ma_version_tag` change marker). "
            "A JIT that compiles the iterator without a version check "
            "would silently observe a stale or partial key set."
        ),
        source='''\
d = {i: i * i for i in range(5)}
caught = []
try:
    for k in d:
        if k == 2:
            d[100] = 10000  # insert during iteration
except RuntimeError:
    caught.append("insert")
# Reset and try a delete
d = {i: i * i for i in range(5)}
try:
    for k in d:
        if k == 2:
            del d[3]  # delete during iteration
except RuntimeError:
    caught.append("delete")
assert caught == ["insert", "delete"], caught
''',
        tags=TagSet.make("containers", type_stability="monomorphic",
                         control_flow="loop", opt_state="deoptimized",
                         tags={"stress", "aliasing", "container", "dict",
                               "mutation-during-iter", "RuntimeError"}),
    ),
    # ------------------------------------------------------------------
    # 7. Mutation during set iteration (must raise).
    # ------------------------------------------------------------------
    T(
        name="mutation_during_set_iteration_raises",
        category="aliasing",
        description=(
            "Same as the dict case but for sets: adding or removing an "
            "element during iteration must raise RuntimeError. The JIT "
            "must keep a generation/version guard on the set."
        ),
        source='''\
s = set(range(5))
caught = []
try:
    for x in s:
        if x == 2:
            s.add(100)
except RuntimeError:
    caught.append("add")
s = set(range(5))
try:
    for x in s:
        if x == 2:
            s.discard(3)
except RuntimeError:
    caught.append("discard")
assert caught == ["add", "discard"], caught
''',
        tags=TagSet.make("containers", type_stability="monomorphic",
                         control_flow="loop", opt_state="deoptimized",
                         tags={"stress", "aliasing", "container", "set",
                               "mutation-during-iter", "RuntimeError"}),
    ),
    # ------------------------------------------------------------------
    # 8. Slice creates a copy (no aliasing).
    # ------------------------------------------------------------------
    T(
        name="list_slice_is_independent_copy",
        category="aliasing",
        description=(
            "Negative case: `xs[:]` returns a fresh list, so mutations "
            "to the slice must NOT propagate to the original. A JIT that "
            "incorrectly treats slicing as an alias would break this."
        ),
        source='''\
xs = [1, 2, 3]
copy = xs[:]
copy.append(4)
assert xs == [1, 2, 3]
assert copy == [1, 2, 3, 4]
assert copy is not xs
copy[0] = 999
assert xs[0] == 1
# But full slice keeps element aliasing for mutable items.
inner = [10]
outer = [inner, 20]
outer_copy = outer[:]
outer_copy[0].append(11)
assert outer[0] == [10, 11]   # element aliasing preserved
assert outer_copy[0] is outer[0]
outer_copy[1] = 999
assert outer[1] == 20          # outer list itself is independent
''',
        tags=TagSet.make("containers", type_stability="monomorphic",
                         control_flow="straight_line", opt_state="hot",
                         tags={"stress", "aliasing", "container", "list",
                               "slice", "shallow-copy"}),
    ),
    # ------------------------------------------------------------------
    # 9. Dict .copy() is shallow (values still alias).
    # ------------------------------------------------------------------
    T(
        name="dict_copy_is_shallow_values_alias",
        category="aliasing",
        description=(
            "`dict.copy()` produces a new dict but the *values* are still "
            "shared references. Mutating a mutable value in place must be "
            "visible through both dicts; replacing a value under a key in "
            "the copy must NOT affect the original."
        ),
        source='''\
shared_list = [1, 2]
d = {"k": shared_list, "n": 5}
c = d.copy()
assert c is not d
assert c["k"] is d["k"]   # value aliasing preserved
# In-place mutation through one alias is visible through the other.
c["k"].append(3)
assert d["k"] == [1, 2, 3]
assert c["k"] == [1, 2, 3]
# Replacing a value under a key in the copy is NOT visible in original.
c["n"] = 99
assert d["n"] == 5
assert c["n"] == 99
# Adding a key in the copy is not visible in original.
c["new"] = "x"
assert "new" not in d
''',
        tags=TagSet.make("containers", type_stability="monomorphic",
                         control_flow="straight_line", opt_state="hot",
                         tags={"stress", "aliasing", "container", "dict",
                               "shallow-copy"}),
    ),
    # ------------------------------------------------------------------
    # 10. Aliasing through a function call.
    # ------------------------------------------------------------------
    T(
        name="aliasing_through_function_arg",
        category="aliasing",
        description=(
            "A list is passed to a function which mutates it. The caller's "
            "list must reflect the mutation. A JIT that inlines the call "
            "and treats the formal parameter as a fresh object (escape-"
            "analysis gone wrong) would miss the side effect."
        ),
        source='''\
def append_sum(xs):
    xs.append(sum(xs))

data = [1, 2, 3]
seen_ids = [id(data)]
append_sum(data)
assert data == [1, 2, 3, 6]
seen_ids.append(id(data))
assert seen_ids[0] == seen_ids[1]   # same object throughout

def extend_in_place(dst, src):
    dst.extend(src)

dst = [0]
src = [1, 2, 3]
extend_in_place(dst, src)
assert dst == [0, 1, 2, 3]
assert src == [1, 2, 3]   # src untouched
''',
        tags=TagSet.make("containers", type_stability="monomorphic",
                         control_flow="straight_line",
                         call_behavior="py_to_py", opt_state="hot",
                         tags={"stress", "aliasing", "container", "function",
                               "escape-analysis"}),
    ),
    # ------------------------------------------------------------------
    # 11. Aliasing through a closure cell.
    # ------------------------------------------------------------------
    T(
        name="aliasing_through_closure_cell",
        category="aliasing",
        description=(
            "A closure captures a list by reference. Mutating the list "
            "from inside the closure must be visible to the enclosing "
            "scope and vice versa. A JIT that box-to-scalar optimizes "
            "the closure variable without recognizing the alias would "
            "miss updates in either direction."
        ),
        source='''\
def make_appender():
    buf = []
    def append(x):
        buf.append(x)
        return len(buf)
    def snapshot():
        return list(buf)
    return append, snapshot, buf

append, snapshot, captured_buf = make_appender()
assert append(1) == 1
assert append(2) == 2
assert snapshot() == [1, 2]
# The closure-captured buf IS the one returned to the caller.
assert captured_buf == [1, 2]
assert captured_buf is not snapshot()  # snapshot returns a copy
# Mutating through the caller's alias is visible to the closure.
captured_buf.append(99)
assert snapshot() == [1, 2, 99]
assert append(3) == 4
assert captured_buf == [1, 2, 99, 3]
''',
        tags=TagSet.make("containers", type_stability="monomorphic",
                         control_flow="straight_line", call_behavior="closure",
                         opt_state="hot",
                         tags={"stress", "aliasing", "closure", "container",
                               "list", "escape-analysis"}),
    ),
    # ------------------------------------------------------------------
    # 12. String interning causing aliasing.
    # ------------------------------------------------------------------
    T(
        name="string_interning_identity_alias",
        category="aliasing",
        description=(
            "`sys.intern` returns the canonical interned string object so "
            "two interns of equal value are the *same object* (`is` True). "
            "A JIT that uses object identity as a fast-path equality check "
            "would silently start returning True for unrelated string "
            "literals that happen to be interned."
        ),
        source='''\
import sys

s1 = sys.intern("hello" + "_world")
s2 = sys.intern("hello_world")
assert s1 is s2
assert s1 == s2
# Non-interned copies of equal value are NOT necessarily identical.
plain_a = "hello_world"
plain_b = "hello_world"
# Literal interned at compile time; both should be the same object here.
assert plain_a is plain_b  # CPython interns small string literals.
# But constructing via runtime concatenation may produce a new object.
parts = ["hello", "_", "world"]
joined = "".join(parts)
assert joined == "hello_world"
# After interning, it becomes identical to the canonical form.
assert sys.intern(joined) is s1
''',
        tags=TagSet.make("strings", type_stability="monomorphic",
                         control_flow="straight_line", opt_state="hot",
                         tags={"stress", "aliasing", "string", "interning",
                               "identity"}),
    ),
    # ------------------------------------------------------------------
    # 13. Small int caching: identity for -5..256.
    # ------------------------------------------------------------------
    T(
        name="small_int_caching_identity",
        category="aliasing",
        description=(
            "CPython pre-caches small ints in the range [-5, 256] so that "
            "any computation producing such a value yields the *same* "
            "object. A JIT that boxes ints on every arithmetic operation "
            "would break `is` checks against cached small ints. Values "
            "outside the cached range may be fresh objects."
        ),
        source='''\
# Inside the cached range: identity holds. We avoid `is <int_literal>`
# directly (which Python warns about) by routing through int() so the
# comparison is between two *computed* values that the JIT cannot fold.
cached_range = list(range(-5, 257))
for n in cached_range:
    a = int(n)
    b = int(n)
    assert a is b, f"identity failed for cached int {n}"

# Just past the cached range, identity is NOT guaranteed.
above = 257
x = int(above)
y = int(above)
assert x == y == 257
# Either identity is fine, but the language does not require it.
assert (x is y) in (True, False)

# Arithmetic results in the cached range still hit the cache.
for n in (0, 1, 100, 200, 256):
    computed = (n - 1) + 1
    assert computed is int(n)

# Identity-equality fast path: two equal interned-ish strings compare
# equal via `is`, but only because they share the cache.
s1 = "abc"
s2 = "abc"
assert s1 is s2   # CPython interns these literals at compile time.
''',
        tags=TagSet.make("numeric", type_stability="monomorphic",
                         control_flow="loop", opt_state="hot",
                         tags={"stress", "aliasing", "int", "cache", "identity"}),
    ),
    # ------------------------------------------------------------------
    # 14. Tuple immutability vs mutable contents.
    # ------------------------------------------------------------------
    T(
        name="tuple_immutable_shell_mutable_contents",
        category="aliasing",
        description=(
            "A tuple's *structure* is immutable, but its elements can be "
            "mutable. Mutating an element through the tuple slot is fine "
            "and visible to other aliases. A JIT that specializes on "
            "`isinstance(x, tuple)` and assumes deep immutability would "
            "get this wrong."
        ),
        source='''\
inner = [2]
t = (1, inner, 3)
# The tuple slot itself is locked.
try:
    t[1] = 99
    assert False, "expected TypeError"
except TypeError:
    pass
# But the object at the slot is mutable.
t[1].append(99)
assert inner == [2, 99]
assert t[1] is inner
assert t == (1, [2, 99], 3)
# Reassignment through the alias still works.
inner.extend([100, 200])
assert t[1] == [2, 99, 100, 200]
# Hashing fails when a tuple contains an unhashable (mutable) element.
try:
    hash(t)
    assert False, "expected TypeError on hash"
except TypeError:
    pass
# But a tuple of immutables is hashable.
t2 = (1, (2, 3), "abc")
assert hash(t2) == hash((1, (2, 3), "abc"))
''',
        tags=TagSet.make("containers", type_stability="monomorphic",
                         control_flow="straight_line", opt_state="hot",
                         tags={"stress", "aliasing", "container", "tuple",
                               "immutability", "hash"}),
    ),
    # ------------------------------------------------------------------
    # 15. Aliasing discovered mid-hot-loop.
    # ------------------------------------------------------------------
    T(
        name="aliasing_discovered_mid_hot_loop",
        category="aliasing",
        description=(
            "A hot loop runs for many iterations with `xs` and `ys` being "
            "distinct objects (so the JIT may speculate they never "
            "alias and hoist `len(xs)` out of the loop). On a later "
            "iteration, the loop body aliases them (`ys = xs`) and then "
            "mutates `xs`; the JIT's hoisted length would now be stale."
        ),
        source='''\
def hot_loop(xs, ys, trigger):
    # `xs` and `ys` start out as distinct, equal-length lists. The JIT
    # may speculate that len(xs) and len(ys) are loop-invariant and
    # hoist them out of the loop. We break that invariant on `trigger`.
    seen_pairs = []
    for i in range(20):
        # These two reads must NOT be hoisted: the alias below changes
        # what len(ys) reports on the very next iteration.
        n_xs = len(xs)
        n_ys = len(ys)
        seen_pairs.append((n_xs, n_ys))
        if i == trigger:
            ys = xs              # ys now aliases xs
            xs.append("marker") # mutates the shared object
            # n_ys for THIS iteration was captured before the alias;
            # but the next iteration must see the growth.
            continue
        if i > trigger + 1:
            break
    return seen_pairs

xs0 = list(range(5))
ys0 = list(range(5))
pairs = hot_loop(xs0, ys0, trigger=3)

# Before the alias: both lengths are 5.
assert pairs[:4] == [(5, 5)] * 4
# On the trigger iteration we capture 5,5 THEN alias+append, so the
# recorded pair for iter 3 is still (5, 5) (length read happened first).
assert pairs[3] == (5, 5)
# After the alias: ys aliases xs, which now has 6 elements.
assert pairs[4] == (6, 6), pairs[4]
assert pairs[5] == (6, 6), pairs[5]
# The marker landed in xs0 (and thus in the now-aliased ys).
assert "marker" in xs0
assert len(xs0) == 6
''',
        tags=TagSet.make("containers", type_stability="monomorphic",
                         control_flow="loop", opt_state="very_hot",
                         tags={"stress", "aliasing", "container", "list",
                               "loop-invariant", "LICM", "hoisting"}),
    ),
]
