"""Type speculation failures.

These stress tests target the JIT's type speculation mechanism: the
compiler observes a few types at a call site or operation, assumes the
next operation will see the same type, and emits a guard. If the guard
fails, the JIT must deoptimize to the interpreter.

Each test below constructs a scenario where the speculation is correct
for a while (allowing the JIT to compile and optimize) and then
deliberately violates the assumption mid-execution.
"""

from __future__ import annotations

from ._shared import T
from ..harness import TagSet


STRESS_TESTS = [
    T(
        name="mono_to_poly_int_to_float",
        category="type_speculation",
        description=(
            "JIT speculates `x + 1` is int+int based on first 100 calls. "
            "The 101st call passes a float, forcing deopt. The deopt must "
            "preserve the correct intermediate value and re-execute in "
            "the interpreter with float semantics."
        ),
        source='''\
def f(x):
    return x + 1

# Warm up monomorphic
results = []
for i in range(100):
    results.append(f(i))

# Speculation breaks here
results.append(f(1.5))
results.append(f(2.5))

# Continue with new type profile
for i in range(100):
    results.append(f(float(i)))

assert results[0] == 1
assert results[100] == 2.5
assert results[-1] == 100.0
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         control_flow="loop", opt_state="deoptimized",
                         tags={"type-speculation", "deopt", "guard-failure"}),
    ),
    T(
        name="mono_to_mega_call_site",
        category="type_speculation",
        description=(
            "A call site `o.f()` is called with the same class for 1000 "
            "iterations, allowing the JIT to inline and emit a monomorphic "
            "inline cache. Then 6 different classes are passed, blowing "
            "past the megamorphic threshold. The IC must transition "
            "mono -> poly -> mega without losing any prior call results."
        ),
        source='''\
class A:
    def f(self): return 1
class B:
    def f(self): return 2
class C:
    def f(self): return 3
class D:
    def f(self): return 4
class E:
    def f(self): return 5
class F:
    def f(self): return 6

def call(o):
    return o.f()

# Warm up monomorphic
s = 0
for _ in range(1000):
    s += call(A())

# Go megamorphic
objs = [A(), B(), C(), D(), E(), F()]
for o in objs * 100:
    s += call(o)

assert s == 1000 + sum(o.f() for o in objs) * 100
''',
        tags=TagSet.make("stress", type_stability="megamorphic",
                         control_flow="loop", call_behavior="method",
                         opt_state="very_hot", tags={"IC", "megamorphic"}),
    ),
    T(
        name="speculate_list_get_tuple",
        category="type_speculation",
        description=(
            "JIT speculates `x[0]` is a list indexing op after seeing "
            "lists. Then a tuple is passed. The deopt must reconstruct "
            "the correct tuple-indexing semantics (which differ in error "
            "messages and negative index handling)."
        ),
        source='''\
def first(x):
    return x[0]

lists = [[i] for i in range(100)]
for l in lists:
    first(l)

# Now pass tuples
tuples = [(i,) for i in range(100)]
for t in tuples:
    first(t)

# And strings
first("hello")

assert first([10, 20]) == 10
assert first((10, 20)) == 10
assert first("hello") == "h"
''',
        tags=TagSet.make("stress", type_stability="polymorphic",
                         opt_state="deoptimized",
                         tags={"type-speculation", "container"}),
    ),
    T(
        name="speculate_int_overflow_to_bigint",
        category="type_speculation",
        description=(
            "JIT speculates `x * 2` fits in a machine int (PyLong with "
            "ob_digit count = 1). After many iterations with small ints, "
            "we pass a value that causes overflow into multi-digit bigint. "
            "The JIT must either deopt or have a correct overflow check "
            "in the generated code."
        ),
        source='''\
def double(x):
    return x * 2

# Warm up with small ints
for i in range(1000):
    double(i)

# Now force overflow
r1 = double(2**62)
r2 = double(2**63)
r3 = double(2**64)
r4 = double(2**127)

assert r1 == 2**63
assert r2 == 2**64
assert r3 == 2**65
assert r4 == 2**128

# Type of result changed mid-stream
assert type(double(1)) is int
assert type(double(2**63)) is int  # Python ints are arbitrary precision
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         control_flow="loop", opt_state="very_hot",
                         tags={"type-speculation", "overflow", "bigint"}),
    ),
    T(
        name="speculate_simple_class_get_subclass",
        category="type_speculation",
        description=(
            "JIT speculates `o.x` is a simple attribute load on class A "
            "with a fixed offset. Then a subclass B that overrides `x` "
            "via a property is passed. The JIT must deopt the inlined "
            "attribute load and call the property descriptor."
        ),
        source='''\
class A:
    def __init__(self, x):
        self.x = x

class B(A):
    @property
    def x(self):
        return 999

def get_x(o):
    return o.x

# Warm up with A
a = A(1)
for _ in range(1000):
    assert get_x(a) == 1

# B() construction will fail because A.__init__ tries to assign self.x
# but B.x is a read-only property. This is exactly the kind of JIT bug
# we're testing: the JIT must handle the AttributeError correctly.
try:
    b = B(42)
    # If construction succeeded (shouldn't), verify property is used
    assert get_x(b) == 999
except AttributeError:
    pass  # expected: property has no setter

# Verify A instances still work after B is defined
a2 = A(7)
assert get_x(a2) == 7
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         call_behavior="method", opt_state="deoptimized",
                         tags={"type-speculation", "descriptor", "inheritance"}),
    ),
    T(
        name="speculate_dict_then_custom_mapping",
        category="type_speculation",
        description=(
            "JIT speculates `d[k]` is dict.__getitem__. Then an object "
            "with __getitem__ is passed. The deopt must call the custom "
            "__getitem__ rather than the inlined dict path."
        ),
        source='''\
class CustomMapping:
    def __getitem__(self, k):
        if k == 'special':
            return 'CUSTOM'
        return 'default'

def lookup(d, k):
    return d[k]

# Warm up with dict
d = {str(i): i for i in range(100)}
for i in range(1000):
    lookup(d, str(i % 100))

# Now pass a custom mapping
cm = CustomMapping()
assert lookup(cm, 'special') == 'CUSTOM'
assert lookup(cm, 'other') == 'default'
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         opt_state="deoptimized",
                         tags={"type-speculation", "descriptor", "container"}),
    ),
    T(
        name="speculate_iter_list_get_generator",
        category="type_speculation",
        description=(
            "JIT speculates `for x in obj` iterates a list (fast path "
            "via PyList_Type). Then a generator is passed. The JIT must "
            "deopt and use the generator's __next__ protocol."
        ),
        source='''\
def consume(obj):
    total = 0
    for x in obj:
        total += x
    return total

# Warm up with list
lst = list(range(100))
for _ in range(1000):
    consume(lst)

# Now pass a generator
def gen(n):
    for i in range(n):
        yield i

assert consume(gen(100)) == 4950
assert consume(gen(10)) == 45
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         control_flow="loop", opt_state="deoptimized",
                         tags={"type-speculation", "iterator", "generator"}),
    ),
    T(
        name="speculate_str_concat_get_int",
        category="type_speculation",
        description=(
            "JIT speculates `a + b` is str+str (fast path via "
            "PyUnicode_Concat). Then int+int is passed. The deopt must "
            "call the correct nb_add slot."
        ),
        source='''\
def add(a, b):
    return a + b

# Warm up str+str
for _ in range(1000):
    add("a", "b")

# Now int+int
assert add(1, 2) == 3
assert add(2**63, 1) == 2**63 + 1

# And float+float
assert add(1.5, 2.5) == 4.0

# And list+list
assert add([1], [2]) == [1, 2]
''',
        tags=TagSet.make("stress", type_stability="megamorphic",
                         opt_state="deoptimized",
                         tags={"type-speculation", "binop", "megamorphic"}),
    ),
    T(
        name="speculate_function_call_then_callable_obj",
        category="type_speculation",
        description=(
            "JIT speculates `f()` is a direct function call. Then a "
            "callable object (with __call__) is passed. The deopt must "
            "use the tp_call slot instead of the inlined function pointer."
        ),
        source='''\
def real_fn():
    return 42

class Callable:
    def __call__(self):
        return 99

def invoke(f):
    return f()

# Warm up with real function
for _ in range(1000):
    invoke(real_fn)

# Now callable object
assert invoke(Callable()) == 99
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         call_behavior="indirect", opt_state="deoptimized",
                         tags={"type-speculation", "callable", "tp_call"}),
    ),
    T(
        name="speculate_return_int_get_none",
        category="type_speculation",
        description=(
            "JIT speculates `f()` returns int and may unbox it. The 101st "
            "call returns None. The deopt must rebox and propagate None "
            "correctly to the caller."
        ),
        source='''\
flag = [False]

def f(x):
    if x < 100:
        return x * 2
    return None

# Warm up returning int
for i in range(100):
    f(i)

# Now return None
assert f(100) is None
assert f(200) is None

# And back to int
assert f(50) == 100
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         opt_state="deoptimized",
                         tags={"type-speculation", "return-type", "unbox"}),
    ),
    T(
        name="speculate_arithmetic_no_exception_get_zerodiv",
        category="type_speculation",
        description=(
            "JIT speculates `a / b` never raises and may elide the "
            "exception check. Then b=0 is passed, raising "
            "ZeroDivisionError. The deopt must catch this."
        ),
        source='''\
def divide(a, b):
    return a / b

# Warm up with non-zero
for i in range(1, 100):
    divide(100, i)

# Now zero
for _ in range(5):
    try:
        divide(1, 0)
        assert False, "should have raised"
    except ZeroDivisionError:
        pass

# Back to normal
assert divide(10, 2) == 5.0
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         control_flow="if_else", opt_state="deoptimized",
                         tags={"type-speculation", "exception", "zerodiv"}),
    ),
    T(
        name="speculate_global_constant_then_mutate",
        category="type_speculation",
        description=(
            "JIT speculates the global `CONST` is the int 42 and may "
            "inline it as a constant. Then the global is mutated. The "
            "JIT must invalidate any compiled code that embedded the "
            "constant."
        ),
        source='''\
CONST = 42

def read_const():
    return CONST + 1

# Warm up
for _ in range(1000):
    assert read_const() == 43

# Mutate global
CONST = 100
assert read_const() == 101

# Mutate again
CONST = -5
assert read_const() == -4

# Back
CONST = 42
assert read_const() == 43
''',
        tags=TagSet.make("stress", type_stability="polymorphic",
                         opt_state="deoptimized",
                         tags={"type-speculation", "global", "invalidation"}),
    ),
    T(
        name="speculate_attribute_offset_then_add_slot",
        category="type_speculation",
        description=(
            "JIT speculates `o.x` is at a fixed memory offset. Then the "
            "class is mutated (a __slots__ entry added or a new class "
            "attribute), invalidating the offset cache. The JIT must "
            "re-lookup the attribute."
        ),
        source='''\
class A:
    __slots__ = ('x', 'y')
    def __init__(self):
        self.x = 1
        self.y = 2

def get_x(o):
    return o.x

a = A()
for _ in range(1000):
    get_x(a)

# Add a class-level attribute (does not change slots but changes MRO)
A.z = 99
assert a.z == 99
assert get_x(a) == 1  # offset should still be valid

# Now shadow x with a property via subclass
class B(A):
    @property
    def x(self):
        return 999

# B() construction will fail because A.__init__ tries to assign self.x
# but B.x is a property without a setter.
try:
    b = B()
    assert False, "should have raised AttributeError"
except AttributeError:
    pass  # expected

# Verify A instances still work
assert get_x(a) == 1
assert B.__mro__ == (B, A, object)
''',
        tags=TagSet.make("stress", type_stability="polymorphic",
                         call_behavior="method", opt_state="deoptimized",
                         tags={"type-speculation", "slots", "descriptor"}),
    ),
    T(
        name="speculate_loop_count_then_unbounded",
        category="type_speculation",
        description=(
            "JIT speculates `range(N)` produces a known-size iterator "
            "and may unroll the loop. Then a generator of unknown size "
            "is passed. The deopt must handle the unbounded iteration."
        ),
        source='''\
def total(it):
    s = 0
    for x in it:
        s += x
    return s

# Warm up with range (known size)
for _ in range(100):
    total(range(100))

# Now generator (unknown size)
def gen():
    i = 0
    while i < 73:  # weird bound
        yield i
        i += 1

assert total(gen()) == sum(range(73))

# And a list
assert total(list(range(50))) == 1225

# And a string (iterates chars)
assert total(ord(c) for c in "abc") == ord('a') + ord('b') + ord('c')
''',
        tags=TagSet.make("stress", type_stability="polymorphic",
                         control_flow="loop", opt_state="deoptimized",
                         tags={"type-speculation", "iterator", "loop-count"}),
    ),
    T(
        name="speculate_comparison_eq_then_custom_eq",
        category="type_speculation",
        description=(
            "JIT speculates `a == b` uses the default __eq__ (pointer "
            "comparison). Then a class with custom __eq__ is passed. The "
            "deopt must call the custom __eq__."
        ),
        source='''\
def eq(a, b):
    return a == b

# Warm up with ints
for _ in range(1000):
    eq(1, 1)

class Weird:
    def __eq__(self, other):
        return True  # always equal

w = Weird()
assert eq(w, 1) is True
assert eq(1, w) is True  # __eq__ reflected
assert eq(w, w) is True
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         opt_state="deoptimized",
                         tags={"type-speculation", "comparison", "descriptor"}),
    ),
]
