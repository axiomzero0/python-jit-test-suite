"""Generator/coroutine stress tests.

Generators and coroutines are among the hardest constructs for a JIT to
support correctly because their execution is *resumable*: the frame must
be suspended at a ``yield`` / ``await`` point and later reconstructed
exactly. Each suspension is a potential OSR exit edge in reverse --- the
compiled frame must be torn down into a resumable interpreter frame, and
on resume the JIT must rebuild (or re-enter) compiled state without
losing locals, block stack, sent values, or pending exception state.

These tests deliberately target specific JIT assumptions about
generators, coroutines, and async generators:

- Yield inside a hot OSR'd loop must reconstruct the frame on each resume.
- ``send()`` must deliver the injected value into the right local after
  a deopt, even when the value's type differs from the speculation.
- ``throw()`` must inject an exception *into* the suspended frame at the
  exact ``yield`` point, not at the caller.
- ``close()`` must raise ``GeneratorExit`` at the yield point and run any
  enclosing ``finally`` blocks.
- ``yield from`` must forward ``send``/``throw``/``close`` to the
  sub-generator and capture the sub-generator's return value as the
  result of the delegation expression.
- Type speculation on yielded values breaks when the generator yields a
  mix of int / float / str / container.
- A generator suspended across a GC cycle must keep its frame alive;
  partial iteration followed by a delayed resume must preserve state.
- Closures captured by generators must be re-read on every resume, not
  cached at compile time.
- Recursive ``yield from`` builds a deep stack of suspended generator
  frames that the runtime must manage without corruption.
- Async generators (``async def`` + ``yield``) and coroutines (``await``)
  exercise the same resumable-frame machinery through the event loop's
  state-machine transitions.
"""

from __future__ import annotations

from ._shared import T
from ..harness import TagSet


STRESS_TESTS = [
    T(
        name="osr_yield_in_hot_loop",
        category="generators",
        description=(
            "A generator yields from inside a hot loop that the JIT will "
            "OSR into. Each ``yield`` suspends the frame mid-loop; on "
            "resume the compiled frame must reconstruct the loop counter, "
            "the accumulator, and the bytecode position exactly. A JIT "
            "that caches loop state across a yield boundary will produce "
            "wrong intermediate values."
        ),
        source='''\
def gen(n):
    acc = 0
    for i in range(n):
        acc += i
        yield acc

# Large enough to trigger OSR inside the generator body.
g = gen(10000)
last = 0
for v in g:
    last = v
assert last == sum(range(10000))

# Spot-check that each resume produced the correct partial sum, proving
# the accumulator and loop counter survive the suspend/resume cycle.
vals = list(gen(1000))
assert vals[0] == 0
assert vals[1] == 1
assert vals[499] == sum(range(500))
assert vals[500] == sum(range(501))
assert vals[-1] == sum(range(1000))
assert len(vals) == 1000
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", call_behavior="generator",
                         opt_state="hot", tags={"generator", "yield", "OSR"}),
    ),
    T(
        name="generator_send_after_deopt",
        category="generators",
        description=(
            "``send()`` injects a value into the generator at the yield "
            "point. The JIT may speculate that the sent value is always "
            "an int; sending a float mid-stream forces a deopt. The sent "
            "value must land in the right local and the accumulator must "
            "transition from int to float without losing precision or "
            "the running total."
        ),
        source='''\
def gen():
    total = 0
    while True:
        v = yield total
        if v is None:
            return
        total += v

g = gen()
assert next(g) == 0          # prime: total starts at 0
assert g.send(10) == 10      # int speculation established
assert g.send(20) == 30      # still int
# Deopt trigger: sent value is now a float.
r = g.send(0.5)
assert r == 30.5
assert isinstance(r, float)
# After deopt the interpreter must keep accumulating correctly.
assert g.send(100) == 130.5
assert isinstance(g.send(0), float)
g.close()
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         control_flow="loop", call_behavior="generator",
                         opt_state="deoptimized",
                         tags={"generator", "send", "deopt"}),
    ),
    T(
        name="generator_throw_propagation",
        category="generators",
        description=(
            "``throw()`` must raise the supplied exception *inside* the "
            "generator's suspended frame at the exact yield point, not "
            "in the caller. A JIT that handles throw by unwinding the "
            "caller's frame will skip the generator's own except handlers "
            "and return the wrong value."
        ),
        source='''\
class Boom(Exception):
    pass

def gen():
    received = []
    while True:
        try:
            x = yield
            received.append(x)
        except Boom:
            received.append("caught")
            return received

g = gen()
next(g)          # prime, suspend at `x = yield`
g.send(1)
g.send(2)
# throw() raises Boom at the yield point; the try/except inside the
# generator must catch it, append "caught", and return received.
try:
    g.throw(Boom, "explode")
except StopIteration as e:
    assert e.value == [1, 2, "caught"]
else:
    raise AssertionError("expected StopIteration carrying the return value")
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", call_behavior="generator",
                         opt_state="hot",
                         tags={"generator", "throw", "exception"}),
    ),
    T(
        name="generator_close_raises_generatorexit",
        category="generators",
        description=(
            "``close()`` must raise ``GeneratorExit`` at the suspended "
            "yield point so that any enclosing ``finally`` runs. A JIT "
            "that tears down the generator frame without synthesizing the "
            "GeneratorExit will skip cleanup. Also verifies that closing "
            "an already-finished generator is a silent no-op."
        ),
        source='''\
cleanup = []

def gen():
    try:
        while True:
            yield 1
    finally:
        cleanup.append("finally")
    # Unreachable, but documents intent.
    yield 2

g = gen()
assert next(g) == 1
assert next(g) == 1
g.close()
assert cleanup == ["finally"]

# Closing an already-closed generator must be a no-op (no second finally).
g.close()
assert cleanup == ["finally"]

# Closing a never-started generator must not run the body at all.
g2 = gen()
g2.close()
assert cleanup == ["finally"]
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="early_exit", call_behavior="generator",
                         opt_state="hot",
                         tags={"generator", "close", "GeneratorExit", "finally"}),
    ),
    T(
        name="yield_from_subgenerator_deopt",
        category="generators",
        description=(
            "Outer generator delegates to an inner generator via "
            "``yield from``. The inner generator deopts mid-stream (a "
            "value of a different type flows through). The deopt must "
            "happen in the inner frame while the outer frame stays "
            "suspended, and every value must still be forwarded to the "
            "consumer in order."
        ),
        source='''\
def inner(values):
    for v in values:
        yield v * 2

def outer(values):
    yield from inner(values)

# Mix ints with a float exactly in the middle to force a deopt in `inner`.
data = list(range(500)) + [0.5] + list(range(500, 1000))
result = list(outer(data))
expected = [v * 2 for v in data]
assert result == expected
assert isinstance(result[0], int)
assert isinstance(result[500], float)
assert isinstance(result[501], int)
assert len(result) == len(data)
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         control_flow="loop", call_behavior="generator",
                         opt_state="deoptimized",
                         tags={"generator", "yield-from", "deopt"}),
    ),
    T(
        name="generator_yields_mixed_types",
        category="generators",
        description=(
            "Type speculation on the yielded value assumes a stable "
            "type. This generator deliberately yields int, then float, "
            "then str, then list, then dict across consecutive yields. "
            "The JIT's yield-site type profile must invalidate and the "
            "consumer must receive each value with its correct type."
        ),
        source='''\
def gen():
    yield 1
    yield 2.5
    yield "three"
    yield [4]
    yield {"five": 5}

values = list(gen())
assert values[0] == 1 and isinstance(values[0], int)
assert values[1] == 2.5 and isinstance(values[1], float)
assert values[2] == "three" and isinstance(values[2], str)
assert values[3] == [4] and isinstance(values[3], list)
assert values[4] == {"five": 5} and isinstance(values[4], dict)

# Re-running must keep producing the same mixed sequence (no stale
# speculation cached across generator instances).
again = list(gen())
assert again == values
''',
        tags=TagSet.make("stress", type_stability="polymorphic",
                         control_flow="straight_line", call_behavior="generator",
                         opt_state="deoptimized",
                         tags={"generator", "yield", "type-speculation"}),
    ),
    T(
        name="generator_survives_gc",
        category="generators",
        description=(
            "A generator is suspended partway through (its frame holds "
            "live references to locals). A GC cycle runs while it is "
            "suspended. The generator frame must survive collection and "
            "all its locals must remain valid on resume. A JIT that "
            "over-eagerly reclaims or relocates the suspended frame "
            "will corrupt the resumed state."
        ),
        source='''\
import gc
import weakref

def gen():
    big = list(range(1000))   # a non-trivial local that the frame pins
    for i in range(10):
        yield big[i]

g = gen()
first = next(g)
second = next(g)

# Hold only a weak ref to the generator and force a full collection.
ref = weakref.ref(g)
# Allocate a lot of garbage to pressure the collector.
_ = [list(range(100)) for _ in range(2000)]
gc.collect()

assert ref() is g, "generator must not be collected while suspended"
third = next(g)
assert first == 0 and second == 1 and third == 2

# Resume after GC: the remaining values must come from the original `big`.
rest = list(g)
assert rest == [3, 4, 5, 6, 7, 8, 9]
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", call_behavior="generator",
                         opt_state="hot",
                         tags={"generator", "GC", "suspension", "weakref"}),
    ),
    T(
        name="nested_generators",
        category="generators",
        description=(
            "A generator that yields from another generator builds two "
            "suspended frames chained together. The outer frame's "
            "yield-from state (which sub-generator it's delegating to) "
            "must be preserved across each resume so values flow through "
            "in the right order with the outer's own bookend yields."
        ),
        source='''\
def inner(n):
    for i in range(n):
        yield ("inner", i)

def outer(n):
    yield ("outer-start", -1)
    yield from inner(n)
    yield ("outer-end", n)

result = list(outer(5))
assert result[0] == ("outer-start", -1)
assert result[1] == ("inner", 0)
assert result[2] == ("inner", 1)
assert result[5] == ("inner", 4)
assert result[6] == ("outer-end", 5)
assert len(result) == 7

# Verify send() is forwarded to the delegated sub-generator, and the
# sub-generator's return value becomes the yield-from result.
def sink():
    acc = 0
    while True:
        v = yield acc
        if v is None:
            return acc
        acc += v

def wrapper():
    total = yield from sink()
    yield ("total", total)

w = wrapper()
assert next(w) == 0          # sink yields acc=0
assert w.send(5) == 5       # acc -> 5, yields 5
assert w.send(10) == 15     # acc -> 15, yields 15
# send(None) makes sink `return acc` (15); yield-from binds total=15;
# wrapper then yields ("total", 15).
assert w.send(None) == ("total", 15)
# wrapper is now exhausted.
try:
    next(w)
    raise AssertionError("expected StopIteration")
except StopIteration:
    pass
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="nested_loop", call_behavior="generator",
                         opt_state="hot",
                         tags={"generator", "yield-from", "nesting"}),
    ),
    T(
        name="generator_try_finally_on_close",
        category="generators",
        description=(
            "``try/finally`` wrapping a ``yield`` must run the finally "
            "block on ``close()`` (GeneratorExit), on normal exhaustion, "
            "and on exception propagation. A JIT that models the block "
            "stack incorrectly during generator teardown will skip the "
            "finally or run it twice."
        ),
        source='''\
log = []

def gen():
    try:
        yield 1
        yield 2
        yield 3
    finally:
        log.append("cleanup")

# Case 1: close() mid-iteration runs finally exactly once.
g = gen()
assert next(g) == 1
assert next(g) == 2
g.close()
assert log == ["cleanup"]

# Case 2: normal exhaustion also runs finally exactly once.
log.clear()
g2 = gen()
assert list(g2) == [1, 2, 3]
assert log == ["cleanup"]

# Case 3: an exception raised inside the body propagates and finally runs.
log.clear()
def gen_exc():
    try:
        yield 1
        raise ValueError("inside")
    finally:
        log.append("cleanup")

g3 = gen_exc()
next(g3)
try:
    next(g3)
except ValueError:
    pass
assert log == ["cleanup"]
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="early_exit", call_behavior="generator",
                         opt_state="hot",
                         tags={"generator", "finally", "close", "exception"}),
    ),
    T(
        name="stopiteration_value_becomes_yield_from_result",
        category="generators",
        description=(
            "When a sub-generator terminates, the value it carries on its "
            "StopIteration becomes the result of the enclosing "
            "``yield from`` expression. A JIT that drops the StopIteration "
            "value (or binds ``None``) will get the wrong result. Tested "
            "both via ``return`` in a generator and via a plain iterator "
            "that explicitly raises ``StopIteration(value)``."
        ),
        source='''\
def sub():
    yield 1
    yield 2
    return "final-value"

def outer():
    result = yield from sub()
    yield ("got", result)

assert list(outer()) == [1, 2, ("got", "final-value")]

# Directly observe the StopIteration.value to confirm the mechanism.
g = sub()
assert next(g) == 1
assert next(g) == 2
try:
    next(g)
except StopIteration as e:
    assert e.value == "final-value"
else:
    raise AssertionError("expected StopIteration")

# A non-generator iterator that raises StopIteration(value) must also
# feed its value into yield from.
class CustomIter:
    def __init__(self, items, final):
        self._items = list(items)
        self._final = final
        self._i = 0
    def __iter__(self):
        return self
    def __next__(self):
        if self._i < len(self._items):
            v = self._items[self._i]
            self._i += 1
            return v
        raise StopIteration(self._final)

def outer2():
    result = yield from CustomIter([1, 2, 3], "done")
    yield result

assert list(outer2()) == [1, 2, 3, "done"]
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="straight_line", call_behavior="generator",
                         opt_state="hot",
                         tags={"generator", "yield-from", "StopIteration"}),
    ),
    T(
        name="async_generator_async_for",
        category="generators",
        description=(
            "An async generator (``async def`` with ``yield``) suspends "
            "on the event loop rather than the bytecode frame, but the "
            "resumable-frame requirement is identical. ``async for`` must "
            "drive the generator through every suspension, and a JIT that "
            "compiles the async-for loop must keep the async generator "
            "frame alive across ``await`` points."
        ),
        source='''\
import asyncio

async def agen(n):
    for i in range(n):
        yield i * i

async def main():
    out = []
    async for x in agen(10):
        out.append(x)
    return out

result = asyncio.run(main())
assert result == [i * i for i in range(10)]
assert len(result) == 10

# Verify the async generator can also be partially consumed and resumed,
# exercising the same frame across an explicit anext()/asend() cycle.
async def consume_partial():
    g = agen(5)
    a = await g.__anext__()
    b = await g.__anext__()
    rest = [v async for v in g]
    return (a, b, rest)

a, b, rest = asyncio.run(consume_partial())
assert (a, b, rest) == (0, 1, [4, 9, 16])
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", call_behavior="async",
                         opt_state="hot",
                         tags={"async-generator", "async-for", "yield"}),
    ),
    T(
        name="coroutine_await_state_machine",
        category="generators",
        description=(
            "A coroutine is a state machine: each ``await`` is a "
            "suspension/resumption edge. The JIT must preserve locals, "
            "the await stack, and exception routing across every edge. "
            "This coroutine awaits several sub-coroutines in sequence "
            "and also verifies that an exception raised after an await "
            "propagates correctly back through the suspension point."
        ),
        source='''\
import asyncio

async def add(a, b):
    await asyncio.sleep(0)   # genuine suspension / state-machine edge
    return a + b

async def compute():
    x = await add(1, 2)
    y = await add(x, 3)
    z = await add(y, 4)
    return z

assert asyncio.run(compute()) == 10

# Exception raised after an await must propagate to the caller, crossing
# the suspension boundary cleanly.
async def faulty():
    await asyncio.sleep(0)
    raise ValueError("boom")

async def caller():
    try:
        await faulty()
    except ValueError as e:
        return f"caught: {e}"

assert asyncio.run(caller()) == "caught: boom"

# A longer chain of awaits stresses repeated state-machine transitions.
async def accumulate(n):
    total = 0
    for i in range(n):
        total = await add(total, i)
    return total

assert asyncio.run(accumulate(100)) == sum(range(100))
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="straight_line", call_behavior="async",
                         opt_state="hot",
                         tags={"coroutine", "await", "state-machine"}),
    ),
    T(
        name="generator_partial_iteration_delayed_resume",
        category="generators",
        description=(
            "A generator is advanced a few steps, then left suspended "
            "while substantial unrelated work runs (including creating "
            "and exhausting many other generators). On resume the "
            "original generator's frame must be intact. A JIT that "
            "reuses generator frame slots aggressively can corrupt the "
            "dormant frame."
        ),
        source='''\
def gen():
    for i in range(5):
        yield i

g = gen()
first = next(g)    # 0
second = next(g)    # 1

# Lots of unrelated generator activity that could pressure frame caches.
others = [list(gen()) for _ in range(500)]
assert all(len(o) == 5 for o in others)
assert others[0] == [0, 1, 2, 3, 4]

# Resume the original generator: its state must be untouched.
third = next(g)    # 2
fourth = next(g)   # 3
fifth = next(g)    # 4

assert (first, second, third, fourth, fifth) == (0, 1, 2, 3, 4)

try:
    next(g)
    raise AssertionError("expected StopIteration")
except StopIteration:
    pass

# Resuming an exhausted generator must keep raising StopIteration.
try:
    next(g)
    raise AssertionError("expected StopIteration again")
except StopIteration:
    pass
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="loop", call_behavior="generator",
                         opt_state="hot",
                         tags={"generator", "suspension", "resume"}),
    ),
    T(
        name="generator_closure_var_changes_between_yields",
        category="generators",
        description=(
            "The generator reads a closure-cell variable on each resume. "
            "Between yields the cell is mutated via a setter. A JIT that "
            "hoists the cell read out of the loop (caching the value at "
            "compile time) will serve stale values after the mutation."
        ),
        source='''\
def make_gen():
    state = 0

    def gen():
        nonlocal state
        while True:
            # Must re-read `state` from the cell on EVERY resume.
            yield state

    def set_state(v):
        nonlocal state
        state = v

    return gen, set_state

gen, set_state = make_gen()
g = gen()

assert next(g) == 0
set_state(42)
assert next(g) == 42          # closure cell was mutated between yields
set_state("changed-type")
assert next(g) == "changed-type"
set_state([1, 2, 3])
assert next(g) == [1, 2, 3]

# A fresh generator sees the latest cell value, not a cached one.
g2 = gen()
assert next(g2) == [1, 2, 3]
g.close()
g2.close()
''',
        tags=TagSet.make("stress", type_stability="polymorphic",
                         control_flow="loop", call_behavior="closure",
                         opt_state="hot",
                         tags={"generator", "closure", "cell", "nonlocal"}),
    ),
    T(
        name="recursive_generator_indirect",
        category="generators",
        description=(
            "A generator that ``yield from``s itself recursively (tree "
            "flattening) builds a chain of suspended generator frames "
            "as deep as the recursion. Each frame must stay independently "
            "resumable and values must percolate up the chain in order. A "
            "deep single-leaf tree stresses the runtime's ability to "
            "manage a tall stack of dormant generator frames."
        ),
        source='''\
def walk_tree(node):
    """Recursively yield every leaf in a nested-list tree."""
    if isinstance(node, list):
        for child in node:
            yield from walk_tree(child)
    else:
        yield node

tree = [1, [2, [3, 4], 5], [6, [7, [8, 9]]], 10]
assert list(walk_tree(tree)) == list(range(1, 11))

# A balanced binary-ish tree of known depth.
def build(depth):
    if depth == 0:
        return depth
    return [build(depth - 1), build(depth - 1)]

leaves = list(walk_tree(build(8)))
assert leaves == [0] * (2 ** 8)
assert len(leaves) == 256

# Deeply nested single-leaf tree: 200 suspended generator frames stacked.
deep = 42
for _ in range(200):
    deep = [deep]
assert list(walk_tree(deep)) == [42]
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="recursion", call_behavior="recursive",
                         opt_state="hot",
                         tags={"generator", "yield-from", "recursion"}),
    ),
]
