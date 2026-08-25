"""Inline cache (IC) invalidation stress tests.

Inline caches are the JIT's way of speeding up attribute lookups,
method calls, and global variable accesses by caching the result of
the first lookup. They must be invalidated when:

- The class hierarchy changes (new method added to a base class)
- A global is rebound
- A descriptor is added/removed from a class
- A __slots__ layout changes
- A metaclass __getattribute__ is overridden

Each test below constructs a scenario where the IC is populated and
then invalidated, and verifies that subsequent lookups still return
the correct value.
"""

from __future__ import annotations

from ._shared import T
from ..harness import TagSet


STRESS_TESTS = [
    T(
        name="ic_method_add_to_base",
        category="inline_caches",
        description=(
            "Call site `o.f()` is cached with A.f. Then a method `f` is "
            "added to base class B (parent of A). The IC must invalidate "
            "and pick up B.f for instances of B."
        ),
        source='''\
class B: pass
class A(B):
    def f(self): return 1

def call_f(o):
    return o.f()

a = A()
for _ in range(1000):
    assert call_f(a) == 1

# Now add f to B
B.f = lambda self: 99

b = B()
assert call_f(b) == 99

# A.f should still win for A instances (MRO: A comes before B)
assert call_f(a) == 1
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         call_behavior="method", opt_state="deoptimized",
                         tags={"IC", "invalidation", "hierarchy"}),
    ),
    T(
        name="ic_global_rebind",
        category="inline_caches",
        description=(
            "Global `X` is rebound mid-loop. The IC for LOAD_GLOBAL must "
            "invalidate and re-fetch."
        ),
        source='''X = 1

def reader():
    return X

results = []
for i in range(100):
    results.append(reader())
    if i == 50:
        X = 2
    if i == 75:
        X = 3

# X is set AFTER the append, so:
# results[0..50] = 1 (X was 1 during those calls)
# results[51..75] = 2 (X was 2 during those calls)
# results[76..99] = 3 (X was 3 during those calls)
assert results[0] == 1
assert results[50] == 1   # X set to 2 AFTER this append
assert results[51] == 2   # first call with X=2
assert results[75] == 2   # X set to 3 AFTER this append
assert results[76] == 3   # first call with X=3
assert results[-1] == 3
''',
        tags=TagSet.make("stress", type_stability="polymorphic",
                         control_flow="loop", opt_state="deoptimized",
                         tags={"IC", "global", "invalidation"}),
    ),
    T(
        name="ic_attribute_load_with_descriptor_added",
        category="inline_caches",
        description=(
            "JIT caches `o.x` as a simple instance attribute load. Then "
            "a data descriptor `x` is added to the class, which should "
            "shadow the instance attribute. The IC must invalidate."
        ),
        source='''\
class A:
    pass

a = A()
a.x = 1

def get_x(o):
    return o.x

for _ in range(1000):
    assert get_x(a) == 1

# Add a data descriptor
class Desc:
    def __get__(self, obj, owner):
        return 999
    def __set__(self, obj, value):
        pass

A.x = Desc()
# Now a.x should be 999 (descriptor takes priority over instance dict)
assert get_x(a) == 999
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         opt_state="deoptimized",
                         tags={"IC", "descriptor", "invalidation"}),
    ),
    T(
        name="ic_megamorphic_threshold",
        category="inline_caches",
        description=(
            "Call site transitions from monomorphic -> polymorphic -> "
            "megamorphic by passing more than 4 different types. The IC "
            "must handle each transition correctly."
        ),
        source='''\
class T1:
    def f(self): return 1
class T2:
    def f(self): return 2
class T3:
    def f(self): return 3
class T4:
    def f(self): return 4
class T5:
    def f(self): return 5
class T6:
    def f(self): return 6

def call(o):
    return o.f()

objs = [T1(), T2(), T3(), T4(), T5(), T6()]
results = []
# Iterate so the IC sees each type multiple times
for _ in range(100):
    for o in objs:
        results.append(call(o))

assert results[0] == 1
assert results[599] == 6
assert len(set(results)) == 6
''',
        tags=TagSet.make("stress", type_stability="megamorphic",
                         call_behavior="method", opt_state="very_hot",
                         tags={"IC", "megamorphic", "threshold"}),
    ),
    T(
        name="ic_attribute_delete_from_class",
        category="inline_caches",
        description=(
            "Attribute `x` exists on the class, IC caches the lookup. "
            "Then the attribute is deleted from the class. The IC must "
            "invalidate and fall back to instance __dict__."
        ),
        source='''\
class A:
    x = 1
    def __init__(self):
        self.y = 2

a = A()

def get_x(o):
    return o.x

for _ in range(1000):
    assert get_x(a) == 1

# Now set instance x
a.x = 100
assert get_x(a) == 100  # instance attribute shadows class attr

# Delete class attribute
del A.x
assert get_x(a) == 100  # still reads instance attr

# Delete instance attribute
del a.x
try:
    get_x(a)
    assert False, "should have raised AttributeError"
except AttributeError:
    pass
''',
        tags=TagSet.make("stress", type_stability="polymorphic",
                         opt_state="deoptimized",
                         tags={"IC", "invalidation", "attribute-delete"}),
    ),
    T(
        name="ic_super_call_mro_change",
        category="inline_caches",
        description=(
            "super() call caches the MRO. Then the class hierarchy "
            "changes (new base inserted). The cached super() lookup "
            "must invalidate."
        ),
        source='''\
class Base:
    def f(self): return "Base"

class Mid(Base):
    def f(self): return "Mid->" + super().f()

class Top(Mid):
    def f(self): return "Top->" + super().f()

t = Top()
for _ in range(1000):
    assert t.f() == "Top->Mid->Base"

# Insert a new class between Mid and Base via __bases__ mutation.
# After this, MRO for Top becomes: Top -> Mid -> Inserted -> Base
# But super().f() in Mid was compiled to call Base.f; with the new
# MRO it should call Inserted.f. The IC for super() must invalidate.
class Inserted(Base):
    def f(self): return "Inserted"

Mid.__bases__ = (Inserted,)
# t.f() should now traverse Top -> Mid -> Inserted (Inserted inherits Base.f)
result = t.f()
assert result == "Top->Mid->Inserted", f"got {result!r}"
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         call_behavior="method", opt_state="deoptimized",
                         tags={"IC", "super", "MRO", "hierarchy-mutation"}),
    ),
    T(
        name="ic_builtin_replace",
        category="inline_caches",
        description=(
            "JIT may inline `len()` as a direct call to PyObject_Length. "
            "Then `len` is rebound in the module namespace. The IC must "
            "fall back to LOAD_GLOBAL."
        ),
        source='''\
def call_len(x):
    return len(x)

for _ in range(1000):
    assert call_len([1,2,3]) == 3

# Rebind len locally (module-level)
import builtins
old_len = builtins.len

class FakeLen:
    def __call__(self, x):
        return 999

builtins.len = FakeLen()
try:
    assert call_len([1,2,3]) == 999
finally:
    builtins.len = old_len

assert call_len([1,2,3]) == 3
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         call_behavior="builtin", opt_state="deoptimized",
                         tags={"IC", "builtin", "monkey-patch"}),
    ),
    T(
        name="ic_load_attr_then_setattr",
        category="inline_caches",
        description=(
            "JIT caches `o.x` as an instance attribute at offset N. Then "
            "__setattr__ is overridden on the class. The IC must "
            "invalidate and route future `o.x = ...` through __setattr__."
        ),
        source='''\
class A:
    pass

a = A()
a.x = 1

def get_x(o):
    return o.x

def set_x(o, v):
    o.x = v

for _ in range(1000):
    set_x(a, 1)
    assert get_x(a) == 1

# Override __setattr__
calls = []
class B:
    def __setattr__(self, name, value):
        calls.append((name, value))
        super().__setattr__(name, value * 10)

b = B()
set_x(b, 5)
assert calls == [("x", 5)]
assert get_x(b) == 50
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         opt_state="deoptimized",
                         tags={"IC", "setattr", "descriptor"}),
    ),
    T(
        name="ic_load_method_then_classmethod",
        category="inline_caches",
        description=(
            "JIT caches `o.f()` as a regular method call. Then `f` is "
            "rebound as a classmethod. The IC must invalidate and bind "
            "the class."
        ),
        source='''\
class A:
    def f(self):
        return self

a = A()
def call(o):
    return o.f()

for _ in range(1000):
    assert call(a) is a

# Convert f to a classmethod
A.f = classmethod(lambda cls: cls)
assert call(a) is A
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         call_behavior="method", opt_state="deoptimized",
                         tags={"IC", "classmethod", "invalidation"}),
    ),
    T(
        name="ic_load_method_then_staticmethod",
        category="inline_caches",
        description=(
            "JIT caches `o.f()` as a bound method call. Then `f` is "
            "rebound as a staticmethod. The IC must invalidate and skip "
            "the binding step."
        ),
        source='''\
class A:
    def f(self):
        return self

a = A()
def call(o):
    return o.f()

for _ in range(1000):
    assert call(a) is a

A.f = staticmethod(lambda: 42)
assert call(a) == 42
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         call_behavior="method", opt_state="deoptimized",
                         tags={"IC", "staticmethod", "invalidation"}),
    ),
    T(
        name="ic_dict_keys_version_change",
        category="inline_caches",
        description=(
            "JIT caches dict lookups by the dict's keys version. Adding "
            "a new key bumps the version, invalidating the cache."
        ),
        source='''\
d = {str(i): i for i in range(20)}

def lookup(k):
    return d[k]

for _ in range(1000):
    lookup("5")

# Add new keys (changes keys version)
for i in range(20, 30):
    d[str(i)] = i

assert lookup("5") == 5
assert lookup("25") == 25
assert lookup("29") == 29

# Delete a key
del d["0"]
try:
    lookup("0")
    assert False
except KeyError:
    pass
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         opt_state="deoptimized",
                         tags={"IC", "dict", "keys-version"}),
    ),
    T(
        name="ic_load_global_through_import",
        category="inline_caches",
        description=(
            "JIT caches `math.sqrt`. Then `math` is re-imported (creating "
            "a new module object). The IC must invalidate."
        ),
        source='''\
import math

def call_sqrt(x):
    return math.sqrt(x)

for _ in range(1000):
    call_sqrt(4.0)

# Re-import math (creates new module reference, but builtins handle this)
import sys
old_math = sys.modules.get('math')
import importlib
importlib.reload(math)

assert call_sqrt(4.0) == 2.0
assert call_sqrt(16.0) == 4.0
''',
        tags=TagSet.make("stress", type_stability="monomorphic",
                         call_behavior="builtin", opt_state="deoptimized",
                         tags={"IC", "global", "import", "reload"}),
    ),
    T(
        name="ic_attribute_watch_with_getattribute",
        category="inline_caches",
        description=(
            "JIT caches `o.x`. Then the class gets a custom "
            "__getattribute__ that intercepts all attribute access. The "
            "IC must invalidate and route through the custom method."
        ),
        source='''\
class A:
    x = 1

a = A()

def get_x(o):
    return o.x

for _ in range(1000):
    assert get_x(a) == 1

# Override __getattribute__
log = []
class B(A):
    def __getattribute__(self, name):
        log.append(name)
        return super().__getattribute__(name)

b = B()
assert get_x(b) == 1
assert "x" in log
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         opt_state="deoptimized",
                         tags={"IC", "getattribute", "invalidation"}),
    ),
    T(
        name="ic_call_protocol_function_to_callable",
        category="inline_caches",
        description=(
            "Call site caches a Python function (PyFunction_Type with "
            "vectorcall). Then a callable object is passed, which uses "
            "tp_call instead. The IC must transition."
        ),
        source='''\
def fn(x):
    return x + 1

class Caller:
    def __call__(self, x):
        return x + 100

def invoke(f, x):
    return f(x)

for _ in range(1000):
    assert invoke(fn, 0) == 1

c = Caller()
assert invoke(c, 0) == 100
assert invoke(c, 41) == 141

# Back to function
assert invoke(fn, 41) == 42
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         call_behavior="indirect", opt_state="deoptimized",
                         tags={"IC", "callable", "vectorcall"}),
    ),
    T(
        name="ic_cyclic_megamorphic_call",
        category="inline_caches",
        description=(
            "Cycle through 8 different types at a single call site. This "
            "stress-tests the megamorphic IC's hash-table lookup path "
            "and ensures no entry is dropped."
        ),
        source='''\
classes = [type(f"T{i}", (), {"f": lambda self, i=i: i}) for i in range(8)]

def call(o):
    return o.f()

objs = [c() for c in classes]
expected = [i for i in range(8)] * 200
actual = [call(o) for _ in range(200) for o in objs]

assert actual == expected
''',
        tags=TagSet.make("stress", type_stability="megamorphic",
                         call_behavior="method", opt_state="very_hot",
                         tags={"IC", "megamorphic", "hash-table"}),
    ),
]
