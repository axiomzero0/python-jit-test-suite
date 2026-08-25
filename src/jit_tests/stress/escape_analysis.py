"""Escape analysis stress tests.

Escape analysis determines whether a heap-allocated object can be
proven to stay confined to the local frame. When it can, the JIT is
free to perform scalar replacement (splitting the object into its
fields and placing each in a register or stack slot) or to eliminate
the allocation entirely. The tests below probe every standard escape
channel (globals, returns, exceptions, containers, closures,
generators, opaque callbacks, weak references) as well as the
conditional and recursive variants where a naive flow-insensitive
analysis would either over-eliminate (producing wrong results) or
under-eliminate (missing the optimization).
"""

from __future__ import annotations

from ._shared import T
from ..harness import TagSet


STRESS_TESTS = [
    T(
        name="no_escape_scalar_replace",
        category="escape_analysis",
        description=(
            "A small mutable object is constructed inside a function, "
            "its fields are read and mutated, and only a derived "
            "primitive value escapes. A correct escape analysis can "
            "scalar-replace the object (no heap allocation is needed). "
            "A buggy analysis that fails to track the field writes "
            "would observe stale field values and produce wrong results."
        ),
        source='''\
class Point:
    __slots__ = ("x", "y")
    def __init__(self, x, y):
        self.x = x
        self.y = y

def translate(p, dx, dy):
    # p never escapes translate(); JIT can scalar-replace it.
    return (p.x + dx, p.y + dy)

def work(n):
    results = []
    for i in range(n):
        # Each Point is local to this iteration; it never leaks.
        p = Point(i, i * 2)
        results.append(translate(p, 1, 1))
    return results

r = work(100)
assert len(r) == 100
assert r[0] == (1, 1)
assert r[50] == (51, 101)
assert r[99] == (100, 199)

# Determinism: re-running must yield identical results.
r2 = work(100)
assert r == r2
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", opt_state="hot",
                         tags={"escape-analysis", "scalar-replacement",
                               "allocation-elimination"}),
    ),
    T(
        name="escape_via_global_assignment",
        category="escape_analysis",
        description=(
            "An object is stored into a module-level global. The JIT "
            "must NOT scalar-replace it: the object outlives the frame "
            "and is observable from any code that reads the global. A "
            "naive analysis that only scans local uses would miss this "
            "escape channel and break identity / mutation semantics."
        ),
        source='''\
class Box:
    __slots__ = ("value",)
    def __init__(self, v):
        self.value = v

last_box = None

def make_box(v):
    global last_box
    b = Box(v)
    last_box = b  # b escapes via the global
    return b.value

assert make_box(1) == 1
assert last_box.value == 1
assert make_box(2) == 2
assert last_box.value == 2

# Distinct heap identities per call: the previous global must be
# untouched when a new Box is stored.
first = last_box        # first -> Box(2)
make_box(3)             # last_box -> Box(3)
assert first is not last_box
assert first.value == 2     # original box untouched by make_box(3)
assert last_box.value == 3
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="straight_line", opt_state="hot",
                         tags={"escape-analysis", "escape-via-global",
                               "identity"}),
    ),
    T(
        name="escape_via_function_return",
        category="escape_analysis",
        description=(
            "An object is constructed inside a function and returned "
            "to the caller. The JIT must heap-allocate it because the "
            "caller can observe identity and outlive the callee frame. "
            "A buggy scalar replacement that promoted the object to "
            "registers would corrupt identity comparisons and field "
            "mutations performed by the caller."
        ),
        source='''\
class Pair:
    __slots__ = ("a", "b")
    def __init__(self, a, b):
        self.a = a
        self.b = b

def make_pair(a, b):
    p = Pair(a, b)
    return p  # escapes via return value

p1 = make_pair(1, 2)
p2 = make_pair(1, 2)
assert p1.a == 1 and p1.b == 2
assert p2.a == 1 and p2.b == 2

# Heap-allocated: distinct identities.
assert p1 is not p2

# Mutating one must not affect the other.
p1.a = 99
assert p1.a == 99
assert p2.a == 1
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="straight_line", opt_state="hot",
                         tags={"escape-analysis", "escape-via-return",
                               "identity"}),
    ),
    T(
        name="escape_via_exception_arg",
        category="escape_analysis",
        description=(
            "An object is raised as the argument of an exception. The "
            "exception object (and its args) is reachable from any "
            "frame that catches the exception, so the JIT must "
            "preserve the heap allocation. A scalar-replaced object "
            "would be visible to the catch block as stale or invalid "
            "memory, breaking the catch handler."
        ),
        source='''\
class Result:
    __slots__ = ("code", "msg")
    def __init__(self, code, msg):
        self.code = code
        self.msg = msg

def work(fail):
    r = Result(0, "ok")
    if fail:
        raise ValueError(r)  # r escapes via exception arg
    return r

# Normal path: r escapes via return.
ok = work(False)
assert ok.code == 0
assert ok.msg == "ok"

# Exception path: r must be the heap object carried by the exception.
try:
    work(True)
    assert False, "should have raised"
except ValueError as exc:
    r = exc.args[0]
    assert isinstance(r, Result)
    assert r.code == 0
    assert r.msg == "ok"
    # Mutating the caught object must persist.
    r.code = 99
    assert r.code == 99
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="if_else", opt_state="hot",
                         tags={"escape-analysis", "escape-via-exception",
                               "exception", "identity"}),
    ),
    T(
        name="escape_via_list_append",
        category="escape_analysis",
        description=(
            "An object is appended to a list that outlives the frame. "
            "The list holds a strong reference, so the object must be "
            "heap-allocated. A buggy analysis that only considered "
            "direct returns would incorrectly eliminate the allocation "
            "and the list would hold garbage."
        ),
        source='''\
class Item:
    __slots__ = ("idx", "tag")
    def __init__(self, idx, tag):
        self.idx = idx
        self.tag = tag

def build_items(n):
    items = []
    for i in range(n):
        it = Item(i, "tag-{}".format(i))
        items.append(it)  # escapes via list
    return items

result = build_items(5)
assert len(result) == 5
assert result[0].idx == 0
assert result[0].tag == "tag-0"
assert result[4].idx == 4
assert result[4].tag == "tag-4"

# Distinct identities.
assert result[0] is not result[1]

# Mutation must be local to each element.
result[0].idx = 999
assert result[1].idx == 1
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", opt_state="hot",
                         tags={"escape-analysis", "escape-via-list",
                               "container", "identity"}),
    ),
    T(
        name="escape_via_closure_capture",
        category="escape_analysis",
        description=(
            "An object is captured by a nested closure that outlives "
            "the outer frame. The closure cell holds a strong reference, "
            "so the object must be heap-allocated. A scalar-replacement "
            "that ignored closure capture would corrupt the captured "
            "state across calls."
        ),
        source='''\
class Counter:
    __slots__ = ("n",)
    def __init__(self):
        self.n = 0

def make_counter(start=0):
    c = Counter()
    c.n = start
    def inc():
        c.n += 1   # mutates the captured object
        return c.n
    return inc  # c escapes via the closure

inc1 = make_counter()
assert inc1() == 1
assert inc1() == 2
assert inc1() == 3

# Independent closure => independent captured state.
inc2 = make_counter(100)
assert inc2() == 101
assert inc1() == 4
assert inc2() == 102
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="straight_line",
                         call_behavior="closure", opt_state="hot",
                         tags={"escape-analysis", "escape-via-closure",
                               "closure", "identity"}),
    ),
    T(
        name="escape_via_generator_yield",
        category="escape_analysis",
        description=(
            "An object is yielded from a generator. The generator "
            "frame is suspended across yields, holding references to "
            "all locals including the just-yielded object. The JIT "
            "must heap-allocate yielded objects because the consumer "
            "can observe their identity after resumption."
        ),
        source='''\
class Snapshot:
    __slots__ = ("value",)
    def __init__(self, v):
        self.value = v

def gen_snapshots(n):
    for i in range(n):
        s = Snapshot(i)
        yield s  # escapes via yield

result = list(gen_snapshots(3))
assert len(result) == 3
assert result[0].value == 0
assert result[1].value == 1
assert result[2].value == 2

# Distinct identities (heap-allocated per yield).
assert result[0] is not result[1]
assert result[1] is not result[2]

# Mutations are local.
result[0].value = 999
assert result[1].value == 1
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop",
                         call_behavior="generator", opt_state="hot",
                         tags={"escape-analysis", "escape-via-generator",
                               "generator", "identity"}),
    ),
    T(
        name="escape_via_opaque_callback",
        category="escape_analysis",
        description=(
            "An object is passed to a callback resolved through a "
            "module-level global at runtime. Because the JIT cannot "
            "statically resolve the call target, it must conservatively "
            "treat the call as a potential escape point. A "
            "flow-insensitive analysis that assumed the inlined "
            "callback was the only one would break when the callback "
            "swaps and stores the argument."
        ),
        source='''\
# A callable resolved at runtime via a global; the JIT cannot
# statically inline the target.
_handler = None

def set_handler(h):
    global _handler
    _handler = h

class Payload:
    __slots__ = ("data",)
    def __init__(self, d):
        self.data = d

def work():
    p = Payload(42)
    # Indirect call through a global; p may escape.
    return _handler(p)

# First handler: reads p but doesn't store it.
set_handler(lambda p: p.data * 2)
assert work() == 84

# Swap handler at runtime; the JIT must re-resolve and still treat
# p as potentially escaping.
set_handler(lambda p: p.data + 100)
assert work() == 142

# Handler that actually stores p, proving the escape is real.
stored = []
def storing_handler(p):
    stored.append(p)
    return p.data
set_handler(storing_handler)
assert work() == 42
assert len(stored) == 1
assert stored[0].data == 42
assert stored[0] is not None
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="straight_line",
                         call_behavior="indirect", opt_state="hot",
                         tags={"escape-analysis", "escape-via-callback",
                               "indirect-call", "identity"}),
    ),
    T(
        name="escape_conditionally_in_branch",
        category="escape_analysis",
        description=(
            "An object escapes only on one branch of an if/else. A "
            "correct escape analysis must conservatively assume the "
            "object escapes on every path where escape is possible. A "
            "buggy analysis that only considered the non-escaping "
            "branch would corrupt the escaping branch."
        ),
        source='''\
class Config:
    __slots__ = ("mode",)
    def __init__(self, m):
        self.mode = m

escaped = []

def work(escape):
    c = Config("normal")
    if escape:
        escaped.append(c)  # c escapes only on this branch
    return c.mode

# Non-escaping path.
assert work(False) == "normal"
assert len(escaped) == 0

# Escaping path.
assert work(True) == "normal"
assert len(escaped) == 1
assert escaped[0].mode == "normal"

# Each escaping call must allocate a distinct object.
prev = escaped[0]
work(True)
assert len(escaped) == 2
assert escaped[0] is prev
assert escaped[1] is not prev
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="if_else", opt_state="hot",
                         tags={"escape-analysis", "conditional-escape",
                               "identity"}),
    ),
    T(
        name="no_escape_in_hot_loop_allocation_elimination",
        category="escape_analysis",
        description=(
            "A loop allocates a fresh object every iteration; the "
            "object never escapes the iteration. A correct escape "
            "analysis can eliminate the allocation entirely (or fold "
            "the fields into scalars). A buggy analysis that did not "
            "track per-iteration lifetime would either keep "
            "allocating (missed optimization) or incorrectly merge "
            "state across iterations (wrong result)."
        ),
        source='''\
class Acc:
    __slots__ = ("total",)
    def __init__(self):
        self.total = 0
    def add(self, x):
        self.total += x

def work(n):
    grand = 0
    for i in range(n):
        # Each Acc is local to this iteration; never escapes.
        a = Acc()
        a.add(i)
        a.add(i * 2)
        grand += a.total
    return grand

# i + 2i = 3i, so per-iteration total is 3*i.
expected = sum(3 * i for i in range(1000))
assert work(1000) == expected
assert work(0) == 0
assert work(1) == 0          # 3 * 0
assert work(2) == 3          # 3 * 0 + 3 * 1
assert work(10) == 3 * sum(range(10))
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", opt_state="very_hot",
                         tags={"escape-analysis", "scalar-replacement",
                               "allocation-elimination", "loop"}),
    ),
    T(
        name="aliased_objects_same_lifetime",
        category="escape_analysis",
        description=(
            "Two objects allocated in the same frame reference each "
            "other (circular aliasing). Both must be heap-allocated "
            "because each is reachable from the other. A buggy "
            "analysis that treated them as independent could "
            "incorrectly scalar-replace one and break the circular "
            "alias chain observed by the caller."
        ),
        source='''\
class Node:
    __slots__ = ("value", "peer")
    def __init__(self, v):
        self.value = v
        self.peer = None

def make_pair():
    a = Node(1)
    b = Node(2)
    a.peer = b
    b.peer = a  # circular reference
    return a  # b is reachable via a.peer

n = make_pair()
assert n.value == 1
assert n.peer.value == 2
# Circular aliasing must be preserved.
assert n.peer.peer is n

# Mutation through the alias must be visible from the other side.
n.peer.value = 99
assert n.peer.value == 99
assert n.peer.peer.value == 1  # n.value unchanged
assert n.peer.peer.peer is n.peer  # navigate back to b
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="straight_line", opt_state="hot",
                         tags={"escape-analysis", "aliasing",
                               "circular-reference", "identity"}),
    ),
    T(
        name="escape_through_try_finally",
        category="escape_analysis",
        description=(
            "An object is allocated in a try block and referenced in "
            "the corresponding finally. The finally runs on every exit "
            "path (normal return, exception, early return), so the "
            "object's lifetime must span the try/finally boundary. A "
            "buggy analysis that scoped lifetime to just the try block "
            "would observe garbage in the finally."
        ),
        source='''\
class Resource:
    __slots__ = ("opened", "closed")
    def __init__(self):
        self.opened = False
        self.closed = False

def work():
    r = Resource()
    try:
        r.opened = True
        # r escapes via return AND must remain live in finally.
        return r
    finally:
        # r must still be the same heap object here.
        r.closed = True

r = work()
assert r.opened is True
assert r.closed is True   # finally ran after the try body

# Also exercise the exception path.
def work_raise():
    r = Resource()
    try:
        r.opened = True
        raise RuntimeError("boom")
    finally:
        r.closed = True
        # Stash for inspection; without this, r would be unreachable
        # after the re-raise and the test could not observe it.
        global _last_resource
        _last_resource = r

_last_resource = None
try:
    work_raise()
    assert False, "should have raised"
except RuntimeError:
    pass

assert _last_resource is not None
assert _last_resource.opened is True
assert _last_resource.closed is True
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="early_exit", opt_state="hot",
                         tags={"escape-analysis", "try-finally",
                               "exception", "lifetime"}),
    ),
    T(
        name="escape_depends_on_runtime_condition",
        category="escape_analysis",
        description=(
            "Whether an object escapes is determined by a runtime "
            "value the JIT cannot predict at compile time. A correct "
            "analysis must conservatively assume the object escapes "
            "and heap-allocate it on every call. A buggy analysis "
            "that speculated on the non-escaping case would corrupt "
            "the state observed through the escaped reference."
        ),
        source='''\
class Buffer:
    __slots__ = ("size", "data")
    def __init__(self, size):
        self.size = size
        self.data = list(range(size))

kept = None

def work(keep):
    b = Buffer(5)
    b.data[0] = 99
    if keep:
        global kept
        kept = b  # escapes conditionally, based on runtime flag
    return sum(b.data)

# Non-escaping path.
total = work(False)
assert total == 99 + 1 + 2 + 3 + 4
assert kept is None

# Escaping path.
total = work(True)
assert total == 99 + 1 + 2 + 3 + 4
assert kept is not None
assert kept.size == 5
assert kept.data[0] == 99
assert kept.data == [99, 1, 2, 3, 4]
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="if_else", opt_state="hot",
                         tags={"escape-analysis", "runtime-condition",
                               "conditional-escape", "identity"}),
    ),
    T(
        name="escape_in_recursive_function",
        category="escape_analysis",
        description=(
            "A recursive function allocates a fresh object per frame "
            "and links it to the result of the recursive call. Each "
            "frame's object must be heap-allocated because it is "
            "returned to the parent frame and observed as a distinct "
            "identity. A buggy analysis that folded frames together "
            "would corrupt the chain."
        ),
        source='''\
class Frame:
    __slots__ = ("depth", "parent")
    def __init__(self, depth, parent=None):
        self.depth = depth
        self.parent = parent

def build_chain(n):
    if n <= 0:
        return None
    parent = build_chain(n - 1)
    f = Frame(n, parent)  # fresh object per frame
    return f

chain = build_chain(5)
assert chain.depth == 5
assert chain.parent.depth == 4
assert chain.parent.parent.depth == 3
assert chain.parent.parent.parent.depth == 2
assert chain.parent.parent.parent.parent.depth == 1
assert chain.parent.parent.parent.parent.parent is None

# Count the chain length.
count = 0
node = chain
while node is not None:
    count += 1
    node = node.parent
assert count == 5

# Each Frame is a distinct heap object.
assert chain is not chain.parent
assert chain.parent is not chain.parent.parent
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="recursion",
                         call_behavior="recursive", opt_state="hot",
                         tags={"escape-analysis", "recursion",
                               "identity", "lifetime"}),
    ),
    T(
        name="escape_via_weakref",
        category="escape_analysis",
        description=(
            "An object is referenced through a weakref. The weakref "
            "implementation requires a heap-allocated object so that "
            "the GC can notify the weakref when the object dies. A "
            "scalar-replacement that eliminated the heap object would "
            "cause the weakref to return None prematurely, breaking "
            "any code that relies on liveness checks."
        ),
        source='''\
import weakref

class Cached:
    # __weakref__ slot is required for the class to participate in
    # weak references when __slots__ is in use.
    __slots__ = ("key", "value", "__weakref__")
    def __init__(self, k, v):
        self.key = k
        self.value = v

def work():
    c = Cached("answer", 42)
    ref = weakref.ref(c)
    # c must stay alive as a heap object while we hold the weakref.
    # If the JIT had eliminated c, ref() would return None here.
    assert ref() is not None
    assert ref().value == 42
    # The weakref must point to the same object as c.
    assert ref() is c
    # Mutations through c must be visible through the weakref.
    c.value = 100
    assert ref().value == 100
    return ref().value

assert work() == 100

# Verify the weakref dies once the strong reference goes away.
def make_only_weak():
    c = Cached("ephemeral", 7)
    ref = weakref.ref(c)
    return ref

import gc
ref = make_only_weak()
gc.collect()
# c is unreachable, so the weakref should now be dead.
assert ref() is None
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="straight_line", opt_state="hot",
                         tags={"escape-analysis", "weakref", "GC",
                               "identity", "lifetime"}),
    ),
]
