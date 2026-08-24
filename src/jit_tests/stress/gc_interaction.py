"""GC interaction stress tests.

These tests target failure modes at the boundary between the JIT
compiler and the garbage collector. The JIT makes assumptions about
object lifetime, allocation elimination (escape analysis), and
reference counting that the GC can invalidate:

- An object the JIT believes is dead may be kept alive by a weakref
  callback, a finalizer, or a reference cycle.
- GC may run mid-loop (triggered by allocation pressure) and must not
  corrupt the deoptimization state the JIT is reconstructing.
- Finalizers (__del__) may resurrect objects, raise exceptions, or run
  more than once if the JIT's lifetime tracking is wrong.
- Weak references must observe object death at the correct moment: not
  too early (before the object is truly unreachable) and not too late
  (after the JIT has recycled the slot for a new allocation).
- Generator frames suspended mid-iteration hold references that the GC
  must trace; closing or dropping the generator must release them.
- Closure cells participating in reference cycles must be collected by
  the cyclic GC, not pinned by the JIT's closure representation.

Each test below constructs one such scenario and asserts the
observable behavior matches the interpreter's contract.
"""

from __future__ import annotations

from ._shared import T
from ..harness import TagSet


STRESS_TESTS = [
    T(
        name="hot_loop_allocation_collected_out_of_scope",
        category="gc_interaction",
        description=(
            "Objects allocated in a hot loop and observed only via weakref "
            "must be collected as soon as the local is rebound. A JIT that "
            "extends the object's lifetime across iterations (e.g. by keeping "
            "a hidden register reference) would leave stale weakrefs alive."
        ),
        source='''\
import gc
import weakref

class Node:
    __slots__ = ("val", "__weakref__")

def hot_loop():
    wrs = []
    for i in range(2000):
        n = Node()
        n.val = i
        wrs.append(weakref.ref(n))
        # n is rebound next iteration; previous instance must die.
    return wrs

refs = hot_loop()
gc.collect()
alive = sum(1 for r in refs if r() is not None)
assert alive == 0, f"{alive} nodes survived GC; JIT may have extended lifetime"
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", opt_state="deoptimized",
                         tags={"GC", "weakref", "lifetime"}),
    ),
    T(
        name="reference_cycle_broken_by_gc",
        category="gc_interaction",
        description=(
            "A reference cycle created in optimized code cannot be collected "
            "by refcounting alone. The cyclic GC must break the cycle and "
            "finalize each participant. If the JIT elided the cycle-breaking "
            "safepoint, the objects would leak."
        ),
        source='''\
import gc

class A:
    count = 0
    def __init__(self):
        A.count += 1
    def __del__(self):
        A.count -= 1

def make_cycle():
    a = A()
    b = A()
    a.partner = b
    b.partner = a
    # a <-> b cycle; neither is reachable once make_cycle returns.

A.count = 0
for _ in range(1000):
    make_cycle()

gc.collect()
assert A.count == 0, f"{A.count} instances leaked; cyclic GC did not break cycle"
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", opt_state="deoptimized",
                         tags={"GC", "cycle", "finalizer"}),
    ),
    T(
        name="weakref_in_optimized_frame_becomes_none",
        category="gc_interaction",
        description=(
            "A weakref captured in an optimized frame must return None once "
            "the referent is collected. If the JIT keeps the referent alive "
            "via a hidden reference (e.g. in a register spilled to the "
            "frame), the weakref would incorrectly return a live object."
        ),
        source='''\
import gc
import weakref

class Resource:
    pass

def work():
    r = Resource()
    wr = weakref.ref(r)
    # Spin to encourage optimization; the JIT must not pin r across this loop.
    total = 0
    for _ in range(2000):
        total += 1
    assert wr() is not None, "referent must be alive during optimized frame"
    assert total == 2000
    return wr

wr = work()
gc.collect()
assert wr() is None, "weakref must return None after referent collected"
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", opt_state="deoptimized",
                         tags={"GC", "weakref", "frame"}),
    ),
    T(
        name="finalizer_runs_exactly_once",
        category="gc_interaction",
        description=(
            "An object with __del__ must have its finalizer called exactly "
            "once when collected. A JIT that double-frees the object (or "
            "fails to mark it as finalized before running the finalizer) "
            "would cause __del__ to run twice or zero times."
        ),
        source='''\
import gc

class Finalized:
    counter = 0
    def __del__(self):
        Finalized.counter += 1

def work():
    for _ in range(1000):
        f = Finalized()
        # f rebound next iteration -> previous instance collected.

gc.collect()
work()
assert Finalized.counter == 1000, (
    f"finalizer ran {Finalized.counter} times, expected 1000"
)
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", opt_state="deoptimized",
                         tags={"GC", "finalizer", "__del__"}),
    ),
    T(
        name="finalizer_that_raises_is_swallowed",
        category="gc_interaction",
        description=(
            "An exception raised in __del__ must be swallowed by the runtime "
            "(printed to stderr, not propagated). If the JIT's finalizer "
            "dispatch let the exception escape into the dealloc path, the "
            "caller would see a spurious RuntimeError."
        ),
        source='''\
import contextlib
import gc
import io

class BadFinalizer:
    count = 0
    def __del__(self):
        BadFinalizer.count += 1
        raise RuntimeError("boom in finalizer")

def work():
    for _ in range(100):
        f = BadFinalizer()

err = io.StringIO()
with contextlib.redirect_stderr(err):
    work()
    gc.collect()

# Finalizer ran for every object.
assert BadFinalizer.count == 100, (
    f"finalizer ran {BadFinalizer.count} times, expected 100"
)
# Exception was printed to stderr, not propagated (reaching here proves it).
output = err.getvalue()
assert (
    "Exception ignored" in output
    or "RuntimeError" in output
    or "boom" in output
), f"expected error in stderr, got: {output!r}"
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", opt_state="deoptimized",
                         tags={"GC", "finalizer", "exception"}),
    ),
    T(
        name="gc_during_deoptimization_completes_correctly",
        category="gc_interaction",
        description=(
            "GC triggered while a frame is being deoptimized must not corrupt "
            "the reconstructed interpreter state. The deopt handler reads "
            "object pointers from the compiled frame; if GC moves or frees "
            "one mid-reconstruction, the interpreter would see garbage."
        ),
        source='''\
import gc

class A:
    def f(self):
        return "a"

class B:
    def f(self):
        return "b"

def call(o):
    # Speculated monomorphic on A; deopt when B appears.
    return o.f()

# Warm up: A only.
a_pool = [A() for _ in range(500)]
for _ in range(3):
    for a in a_pool:
        assert call(a) == "a"

# Now interleave B (deopt trigger) with manual GC.
results = []
for i in range(1000):
    obj = B() if i % 2 == 0 else A()
    results.append(call(obj))
    if i % 50 == 0:
        gc.collect()

assert results.count("a") == 500
assert results.count("b") == 500
# Sanity: original A pool still works after all the deopt + GC churn.
for a in a_pool:
    assert call(a) == "a"
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         control_flow="loop", opt_state="deoptimized",
                         tags={"GC", "deopt", "safepoint"}),
    ),
    T(
        name="weakref_callback_sees_consistent_state",
        category="gc_interaction",
        description=(
            "A weakref callback fires during GC. At callback time the "
            "referent is already gone, so ref() must return None. If the JIT "
            "delays weakref clearing until after the slot is reused, the "
            "callback could see a different (recycled) object."
        ),
        source='''\
import gc
import weakref

class Obj:
    __slots__ = ("id", "__weakref__")

seen = []
def callback(ref):
    # Must observe None: the referent is dead by callback time.
    seen.append(ref() is None)

def work():
    wrs = []
    for i in range(1000):
        o = Obj()
        o.id = i
        # Keep the weakref alive so the callback fires when o is rebound.
        wrs.append(weakref.ref(o, callback))
    return wrs

wrs = work()
gc.collect()
assert len(seen) == 1000, f"only {len(seen)} callbacks fired"
assert all(seen), "callback observed non-None referent during GC"
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", opt_state="deoptimized",
                         tags={"GC", "weakref", "callback"}),
    ),
    T(
        name="large_allocation_triggers_gc_mid_loop",
        category="gc_interaction",
        description=(
            "Allocating large objects mid-loop can trigger an incremental "
            "GC or a full collection. The collection must not corrupt the "
            "in-progress computation: every list's contents must remain "
            "intact and reachable afterwards."
        ),
        source='''\
import gc

gc.collect()
was_enabled = gc.isenabled()
gc.disable()
try:
    held = []
    totals = []
    for i in range(200):
        # ~40KB list per iteration; 200 of these pressure the GC.
        big = [j * i for j in range(5000)]
        if i % 2 == 0:
            held.append(big)
        totals.append(sum(big))
        # Manual GC mid-loop simulates the runtime's automatic trigger.
        if i % 50 == 49:
            gc.collect()
finally:
    if was_enabled:
        gc.enable()

assert len(held) == 100
assert all(t >= 0 for t in totals)
assert totals[0] == 0
assert totals[1] == sum(range(5000))
assert totals[-1] == 199 * sum(range(5000))
# Verify held lists are intact (GC did not recycle their storage).
for k, lst in enumerate(held):
    assert len(lst) == 5000
    assert lst[0] == 0
    assert lst[-1] == 4999 * (2 * k)
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", opt_state="deoptimized",
                         tags={"GC", "allocation", "large-object"}),
    ),
    T(
        name="escape_via_weakref_prevents_allocation_elimination",
        category="gc_interaction",
        description=(
            "If the JIT's escape analysis sees an object only used locally "
            "it may eliminate the allocation. But if a weakref observes the "
            "object's identity, the allocation must survive: the weakref "
            "must see a distinct object per iteration."
        ),
        source='''\
import gc
import weakref

class Escapee:
    counter = 0
    def __init__(self):
        Escapee.counter += 1

def work():
    wrs = []
    for _ in range(1000):
        e = Escapee()
        # The weakref observes e's identity -> allocation cannot be
        # eliminated by escape analysis.
        wrs.append(weakref.ref(e))
    return wrs

Escapee.counter = 0
wrs = work()
assert Escapee.counter == 1000, (
    f"only {Escapee.counter} allocations; escape analysis wrongly elided"
)
gc.collect()
alive = sum(1 for r in wrs if r() is not None)
assert alive == 0, f"{alive} objects survived; lifetime extended past scope"
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", opt_state="deoptimized",
                         tags={"GC", "weakref", "escape-analysis"}),
    ),
    T(
        name="finalizer_resurrects_object_keeps_alive",
        category="gc_interaction",
        description=(
            "A __del__ that stores self into a global resurrects the object. "
            "The runtime must honor the new reference: a second GC pass must "
            "not collect the resurrected object. A JIT that finalized the "
            "object 'in place' without checking for resurrection would free "
            "memory still reachable from the global."
        ),
        source='''\
import gc

resurrected = []

class Zombie:
    resurrect_allowed = True
    def __del__(self):
        if Zombie.resurrect_allowed:
            # Resurrect: create a new strong reference via the global list.
            resurrected.append(self)

def work():
    for _ in range(100):
        z = Zombie()

work()
gc.collect()
assert len(resurrected) == 100, (
    f"only {len(resurrected)} resurrected, expected 100"
)
# A second GC must not collect them: they are reachable from the global.
gc.collect()
assert len(resurrected) == 100, "resurrected objects collected prematurely"
# Verify they are still functional objects.
for z in resurrected:
    assert isinstance(z, Zombie)
# Disable resurrection so cleanup does not re-add objects.
Zombie.resurrect_allowed = False
resurrected.clear()
gc.collect()
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", opt_state="deoptimized",
                         tags={"GC", "finalizer", "resurrection"}),
    ),
    T(
        name="cycle_with_finalizer_still_finalized",
        category="gc_interaction",
        description=(
            "Objects in a reference cycle that each have __del__ must still "
            "be finalized by the cyclic GC. A JIT that assumes 'cycle => no "
            "finalizer' would leak the objects (or skip their __del__)."
        ),
        source='''\
import gc

class CyclicFinal:
    counter = 0
    def __init__(self):
        CyclicFinal.counter += 1
    def __del__(self):
        CyclicFinal.counter -= 1

def make_cycle():
    a = CyclicFinal()
    b = CyclicFinal()
    a.partner = b
    b.partner = a

gc.collect()
CyclicFinal.counter = 0
for _ in range(1000):
    make_cycle()

gc.collect()
assert CyclicFinal.counter == 0, (
    f"{CyclicFinal.counter} instances leaked; cycle finalizer did not run"
)
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", opt_state="deoptimized",
                         tags={"GC", "cycle", "finalizer"}),
    ),
    T(
        name="suspended_generator_frame_cleaned_up",
        category="gc_interaction",
        description=(
            "A generator suspended mid-iteration holds a frame with live "
            "locals. When the generator is dropped, GC must finalize the "
            "frame and release the locals. A JIT that pinned the frame for "
            "OSR would leak them."
        ),
        source='''\
import gc

class Tracker:
    instances = 0
    def __init__(self):
        Tracker.instances += 1
    def __del__(self):
        Tracker.instances -= 1

def gen():
    t = Tracker()
    while True:
        yield t

# Create and start (but do not exhaust) many generators.
gens = [gen() for _ in range(100)]
for g in gens:
    next(g)

assert Tracker.instances == 100, "each generator should hold one Tracker"

# Drop all generator references; suspended frames must be cleaned up.
# `del g` releases the loop variable's hold on the last generator so GC
# can reclaim it (otherwise the test leaks exactly one frame).
del g
gens.clear()
gc.collect()
assert Tracker.instances == 0, (
    f"{Tracker.instances} trackers leaked from suspended generator frames"
)
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", call_behavior="generator",
                         opt_state="deoptimized",
                         tags={"GC", "generator", "frame"}),
    ),
    T(
        name="closure_cell_in_reference_cycle_collected",
        category="gc_interaction",
        description=(
            "A closure cell that participates in a reference cycle (the "
            "captured variable points back at the closure) must be collected "
            "by the cyclic GC. A JIT that represented the closure cell as a "
            "raw pointer (breaking GC tracing) would leak it."
        ),
        source='''\
import gc

class CountingCell:
    count = 0
    def __init__(self):
        CountingCell.count += 1
    def __del__(self):
        CountingCell.count -= 1

def make_closure_cycle():
    c = CountingCell()
    def inner():
        return c  # closure captures c
    c.callback = inner  # cycle: c -> inner.__closure__ -> c
    return inner

CountingCell.count = 0
fns = [make_closure_cycle() for _ in range(100)]
for f in fns:
    assert isinstance(f(), CountingCell)
assert CountingCell.count == 100

# `del f` releases the loop variable's hold on the last closure so the
# final cycle is collectible (otherwise exactly one cycle leaks).
del f
fns.clear()
gc.collect()
assert CountingCell.count == 0, (
    f"{CountingCell.count} closure cells leaked in cycle"
)
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", call_behavior="closure",
                         opt_state="deoptimized",
                         tags={"GC", "closure", "cycle"}),
    ),
    T(
        name="allocation_eliminated_unless_it_escapes",
        category="gc_interaction",
        description=(
            "An object allocated, used, and discarded in a single function "
            "may be eliminated by escape analysis. But if it escapes (here, "
            "via a weakref), the allocation must survive and the GC must see "
            "it. The test verifies both: in CPython the no-escape path "
            "allocates 1000 objects (correct, if not optimized), and the "
            "escape path allocates 1000 AND collects them after scope exit."
        ),
        source='''\
import gc
import weakref

class Hidden:
    counter = 0
    def __init__(self):
        Hidden.counter += 1

# Case 1: no escape. JIT may eliminate; CPython allocates all.
def no_escape():
    total = 0
    for _ in range(1000):
        h = Hidden()
        total += id(h) & 7  # use but do not store
    return total

Hidden.counter = 0
no_escape()
assert Hidden.counter == 1000  # CPython baseline; JIT may reduce this.

# Case 2: escapes via weakref. JIT must NOT eliminate.
def escapes_via_weakref():
    wrs = []
    for _ in range(1000):
        h = Hidden()
        wrs.append(weakref.ref(h))
    return wrs

Hidden.counter = 0
wrs = escapes_via_weakref()
assert Hidden.counter == 1000, (
    f"only {Hidden.counter} allocations; weakref escape was wrongly elided"
)
gc.collect()
alive = sum(1 for r in wrs if r() is not None)
assert alive == 0, f"{alive} objects survived after scope exit"
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", opt_state="deoptimized",
                         tags={"GC", "escape-analysis", "weakref"}),
    ),
    T(
        name="gc_identifies_live_set_amid_mixed_lifetime",
        category="gc_interaction",
        description=(
            "In a loop allocating many objects where some are kept alive "
            "via a list and others are not, the GC must correctly identify "
            "the live set. A JIT that confused the two sets (e.g. by sharing "
            "a backing store) would either leak dead objects or prematurely "
            "collect live ones."
        ),
        source='''\
import gc
import weakref

class Item:
    __slots__ = ("idx", "__weakref__")

def work():
    kept = []
    dead_wrs = []
    for i in range(2000):
        it = Item()
        it.idx = i
        if i % 2 == 0:
            kept.append(it)
        else:
            dead_wrs.append(weakref.ref(it))
    return kept, dead_wrs

kept, dead_wrs = work()
gc.collect()

# Live set: exactly the 1000 kept items.
assert len(kept) == 1000
assert all(it.idx % 2 == 0 for it in kept)

# Dead set: every other object must be gone.
dead_alive = sum(1 for r in dead_wrs if r() is not None)
assert dead_alive == 0, f"{dead_alive} dead items survived GC"

# Now drop the kept list; those too must become collectible.
kept_wrs = [weakref.ref(it) for it in kept]
kept.clear()
gc.collect()
kept_alive = sum(1 for r in kept_wrs if r() is not None)
assert kept_alive == 0, f"{kept_alive} kept items survived after drop"
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", opt_state="deoptimized",
                         tags={"GC", "live-set", "weakref"}),
    ),
]
