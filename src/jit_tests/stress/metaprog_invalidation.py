"""Metaprogramming invalidation stress tests.

These tests target the JIT's assumptions about runtime structures:
classes, methods, function code objects, globals, builtins. A JIT
caches the result of attribute lookups, global loads, and call-site
resolution in inline caches. Those caches must be invalidated when
the underlying runtime structures change.

Failure modes covered:
- Monkey-patching a class method mid-loop (IC must invalidate)
- Adding a new attribute to a class mid-loop (lookup must find it)
- Changing a class's __bases__ (MRO must update)
- Replacing a function's __code__ (call must use the new code)
- Modifying class state via type.__setattr__ (IC must see it)
- Wrapping an existing method with a decorator at runtime
- Swapping an instance's __class__ at runtime (closest analogue to
  changing the metaclass; CPython forbids reassigning a class's
  metaclass after creation)
- Dynamically creating a new class with type() and using it
- Modifying a function's __defaults__
- Replacing a builtin in the builtins module
- Adding a data descriptor to a class that previously had none
- Creating subclasses with different __slots__ layouts
- Importing a name that shadows an existing global
- Modifying the contents of a function's closure cells directly
- Using exec() to define new functions/classes and invoking them
"""

from __future__ import annotations

from ._shared import T
from ..harness import TagSet


STRESS_TESTS = [
    T(
        name="monkey_patch_method_in_loop",
        category="metaprog_invalidation",
        description=(
            "A method call site runs monomorphic for several iterations "
            "so the JIT caches `C.f`. Mid-loop the class method is "
            "replaced with a new function. The IC must invalidate and "
            "subsequent calls must dispatch to the new method."
        ),
        source='''\
class C:
    def f(self):
        return 1

c = C()
results = []
for i in range(10):
    results.append(c.f())
    if i == 4:
        C.f = lambda self: 99

# First 5 calls saw the original; last 5 saw the patch
assert results[:5] == [1, 1, 1, 1, 1]
assert results[5:] == [99, 99, 99, 99, 99]

# After the loop, the patch persists
assert c.f() == 99

# Restore original
C.f = lambda self: 1
assert c.f() == 1
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         control_flow="loop", call_behavior="method",
                         opt_state="deoptimized",
                         tags={"IC", "invalidation", "monkey-patch"}),
    ),
    T(
        name="add_class_attribute_mid_loop",
        category="metaprog_invalidation",
        description=(
            "A class starts with no attribute `x`. Attribute lookups must "
            "raise AttributeError. Mid-loop, `x` is added to the class. "
            "Existing instances must immediately see the new attribute via "
            "class fallback."
        ),
        source='''\
class C:
    pass

c = C()

# Before: attribute lookup fails
try:
    _ = c.x
    assert False, "expected AttributeError"
except AttributeError:
    pass

results = []
for i in range(10):
    if i == 5:
        C.x = 42
    if hasattr(c, 'x'):
        results.append(c.x)
    else:
        results.append(None)

assert results == [None, None, None, None, None, 42, 42, 42, 42, 42]

# Override the class attribute on the instance
c.x = 7
assert c.x == 7

# Remove the class attribute; instance attr still wins
del C.x
assert c.x == 7

# A fresh instance now has no x
c2 = C()
try:
    _ = c2.x
    assert False
except AttributeError:
    pass
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         control_flow="loop", call_behavior="method",
                         opt_state="deoptimized",
                         tags={"IC", "invalidation", "attribute"}),
    ),
    T(
        name="change_class_bases",
        category="metaprog_invalidation",
        description=(
            "Assigning to C.__bases__ swaps the base class. The MRO must "
            "be recomputed and method dispatch must reflect the new base. "
            "A JIT that cached the old MRO would dispatch to the wrong "
            "method."
        ),
        source='''\
class A:
    def f(self):
        return 'A'

class B:
    def f(self):
        return 'B'

class C(A):
    pass

c = C()
assert c.f() == 'A'
assert C.__mro__ == (C, A, object)

# Swap base
C.__bases__ = (B,)
assert c.f() == 'B'
assert C.__mro__ == (C, B, object)

# Swap back
C.__bases__ = (A,)
assert c.f() == 'A'
assert C.__mro__ == (C, A, object)
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         call_behavior="method", opt_state="deoptimized",
                         tags={"IC", "invalidation", "bases", "MRO"}),
    ),
    T(
        name="replace_function_code",
        category="metaprog_invalidation",
        description=(
            "A function's __code__ is replaced with the code of another "
            "function. Calls to the original name must execute the new "
            "bytecode. The JIT cannot cache the original code pointer."
        ),
        source='''\
def f():
    return 1

def g():
    return 2

assert f() == 1
assert g() == 2

# Swap code
original_code = f.__code__
f.__code__ = g.__code__
assert f() == 2
assert g() == 2  # g is unaffected

# Swap back
f.__code__ = original_code
assert f() == 1

# Now swap with a function that takes an argument
def h(x):
    return x * 10

f.__code__ = h.__code__
assert f(5) == 50
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         call_behavior="direct", opt_state="deoptimized",
                         tags={"invalidation", "code-object", "function"}),
    ),
    T(
        name="modify_class_dict_via_type_setattr",
        category="metaprog_invalidation",
        description=(
            "Class state is mutated via type.__setattr__, which is the "
            "C-level path used by `C.x = ...`. Inline caches that cached "
            "the absence of an attribute must invalidate so the next "
            "lookup finds the new attribute."
        ),
        source='''\
class C:
    pass

c = C()
# Initial: no class attribute, no instance attribute
try:
    _ = c.x
    assert False, "expected AttributeError"
except AttributeError:
    pass

# Direct type-level mutation
type.__setattr__(C, 'x', 42)
assert c.x == 42

# Mutate again
type.__setattr__(C, 'x', 99)
assert c.x == 99

# Add a method via type.__setattr__
type.__setattr__(C, 'greet', lambda self: 'hi')
assert c.greet() == 'hi'

# Delete via type.__delattr__
type.__delattr__(C, 'x')
try:
    _ = c.x
    assert False, "expected AttributeError after deletion"
except AttributeError:
    pass
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         call_behavior="method", opt_state="deoptimized",
                         tags={"IC", "invalidation", "type-setattr"}),
    ),
    T(
        name="decorate_method_at_runtime",
        category="metaprog_invalidation",
        description=(
            "An existing method is wrapped with a decorator at runtime. "
            "Subsequent calls must invoke the wrapper, which itself calls "
            "the original. The IC for `c.f()` must invalidate to pick up "
            "the new wrapper as the resolved method."
        ),
        source='''\
class C:
    def f(self):
        return 1

c = C()
assert c.f() == 1

# Capture original method
original = C.f

def deco(fn):
    def wrapper(self):
        return fn(self) + 100
    return wrapper

# Wrap at runtime
C.f = deco(C.f)
assert c.f() == 101

# Double-wrap: wrapper calls previous wrapper, adding another 100
C.f = deco(C.f)
assert c.f() == 201

# Remove wrapping, restore original
C.f = original
assert c.f() == 1
''',
        tags=TagSet.make("stress", type_stability="polymorphic",
                         call_behavior="method", opt_state="deoptimized",
                         tags={"IC", "invalidation", "decorator"}),
    ),
    T(
        name="swap_instance_class",
        category="metaprog_invalidation",
        description=(
            "An instance's __class__ is reassigned at runtime, swapping "
            "its method dispatch table. CPython forbids reassigning a "
            "class's metaclass after creation, so this is the closest "
            "executable analogue: changing which class an instance "
            "believes it belongs to, which flips all attribute lookups."
        ),
        source='''\
class Base:
    pass

class A(Base):
    kind = 'A'
    def f(self):
        return 1

class B(Base):
    kind = 'B'
    def f(self):
        return 2

obj = A()
results = []
results.append(obj.f())
results.append(obj.kind)

# Swap to B
obj.__class__ = B
results.append(obj.f())
results.append(obj.kind)

# Swap back to A
obj.__class__ = A
results.append(obj.f())
results.append(obj.kind)

assert results == [1, 'A', 2, 'B', 1, 'A']
assert isinstance(obj, A)
assert not isinstance(obj, B)
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         call_behavior="method", opt_state="deoptimized",
                         tags={"invalidation", "instance-class", "swap"}),
    ),
    T(
        name="dynamic_class_via_type_call",
        category="metaprog_invalidation",
        description=(
            "A new class is created by calling type(name, bases, dict) "
            "and used immediately. The JIT cannot have any precompiled "
            "cache for this brand-new class; lookups must resolve via "
            "the freshly built MRO."
        ),
        source='''\
class Base:
    def hello(self):
        return 'base'

def make_class(name, methods):
    return type(name, (Base,), methods)

C = make_class('C', {'hello': lambda self: 'derived'})
c = C()
assert c.hello() == 'derived'
assert isinstance(c, Base)

# Build many distinct classes in a loop
classes = []
for i in range(10):
    methods = {'hello': lambda self, n=i: f'class-{n}'}
    classes.append(make_class(f'C{i}', methods))

for i, cls in enumerate(classes):
    inst = cls()
    assert inst.hello() == f'class-{i}'
    assert isinstance(inst, Base)

# Each class is distinct
assert len({id(c) for c in classes}) == 10
''',
        tags=TagSet.make("stress", type_stability="megamorphic",
                         call_behavior="method", opt_state="very_hot",
                         tags={"invalidation", "type-call", "dynamic-class"}),
    ),
    T(
        name="modify_function_defaults",
        category="metaprog_invalidation",
        description=(
            "A function's __defaults__ tuple is replaced mid-program. "
            "Subsequent calls must use the new defaults, not the ones "
            "captured at def time."
        ),
        source='''\
def f(a, b=10):
    return a + b

assert f(1) == 11
assert f(1, 20) == 21

# Replace defaults
f.__defaults__ = (99,)
assert f(1) == 100

# Replace with different value
f.__defaults__ = (0,)
assert f(1) == 1

# Remove defaults entirely
f.__defaults__ = None
try:
    f(1)
    assert False, "expected TypeError for missing arg"
except TypeError:
    pass
assert f(1, 2) == 3

# Restore
f.__defaults__ = (10,)
assert f(1) == 11
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         call_behavior="direct", opt_state="deoptimized",
                         tags={"invalidation", "defaults", "function"}),
    ),
    T(
        name="replace_builtin_len",
        category="metaprog_invalidation",
        description=(
            "The `len` builtin is replaced in the builtins module. "
            "LOAD_GLOBAL for `len` must re-resolve through builtins and "
            "pick up the new value. A JIT that cached `len = builtins.len` "
            "would dispatch to the original."
        ),
        source='''\
import builtins

orig_len = builtins.len
results = []
try:
    # Sanity: original works
    assert len([1, 2, 3]) == 3

    # Replace with a stub
    builtins.len = lambda x: -1
    results.append(len([1, 2, 3]))

    # Replace with another stub
    builtins.len = lambda x: 999
    results.append(len("hello"))

    # Restore mid-program; subsequent calls use original
    builtins.len = orig_len
    results.append(len([1, 2, 3]))
finally:
    # Always restore to avoid breaking the rest of the suite
    builtins.len = orig_len

assert results == [-1, 999, 3]
assert len([1, 2, 3]) == 3
assert len("hello") == 5
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         call_behavior="builtin", opt_state="deoptimized",
                         tags={"IC", "invalidation", "builtins", "global"}),
    ),
    T(
        name="add_data_descriptor_to_class",
        category="metaprog_invalidation",
        description=(
            "A class starts with a plain instance attribute. A data "
            "descriptor is then added to the class with the same name. "
            "Data descriptors take precedence over instance __dict__, so "
            "subsequent attribute access must invoke the descriptor's "
            "__get__ rather than reading the instance dict."
        ),
        source='''\
class C:
    pass

c = C()
c.x = 1  # plain instance attribute
assert c.x == 1

# Add a data descriptor to the class
class Desc:
    def __get__(self, obj, owner):
        if obj is None:
            return self
        return 999
    def __set__(self, obj, val):
        # Silently store elsewhere; not in obj.__dict__
        obj.__dict__['x_shadow'] = val

C.x = Desc()

# Data descriptor shadows the instance attribute
assert c.x == 999
# The instance __dict__ still has the old value, but it's hidden
assert c.__dict__.get('x') == 1

# Assignment invokes the descriptor's __set__, not __dict__ update
c.x = 42
assert c.__dict__.get('x_shadow') == 42
assert c.x == 999  # still hits the descriptor

# Remove the descriptor; instance attr reappears
del C.x
assert c.x == 1
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         call_behavior="method", opt_state="deoptimized",
                         tags={"IC", "invalidation", "descriptor", "precedence"}),
    ),
    T(
        name="subclass_with_different_slots",
        category="metaprog_invalidation",
        description=(
            "Subclasses of a slotted parent can add or omit slots, "
            "changing the instance memory layout. The JIT must respect "
            "the per-class layout when accessing slotted attributes."
        ),
        source='''\
class A:
    __slots__ = ('x',)

a = A()
a.x = 1
assert a.x == 1

# A has no __dict__; dynamic attributes are forbidden
try:
    a.dynamic = 5
    assert False, "expected AttributeError"
except AttributeError:
    pass

# Subclass with additional slots
class B(A):
    __slots__ = ('y', 'z')

b = B()
b.x = 10
b.y = 20
b.z = 30
assert (b.x, b.y, b.z) == (10, 20, 30)
try:
    b.dynamic = 99
    assert False
except AttributeError:
    pass

# Subclass that explicitly opts into __dict__
class C(A):
    __slots__ = ('__dict__', 'w')

c = C()
c.x = 100
c.w = 200
c.dynamic = 300  # allowed now via __dict__
assert (c.x, c.w, c.dynamic) == (100, 200, 300)

# Subclass with empty __slots__ inherits A's layout, no __dict__
class D(A):
    __slots__ = ()

d = D()
d.x = 7
try:
    d.dynamic = 8
    assert False
except AttributeError:
    pass
''',
        tags=TagSet.make("stress", type_stability="polymorphic",
                         call_behavior="method", opt_state="deoptimized",
                         tags={"invalidation", "slots", "layout"}),
    ),
    T(
        name="import_shadows_global",
        category="metaprog_invalidation",
        description=(
            "A name is bound in the module namespace as a local value. "
            "A subsequent `from X import name` rebinds that name to a "
            "different value. LOAD_NAME / LOAD_GLOBAL must observe the "
            "new binding."
        ),
        source='''\
# Bind a local "pi"
pi = 3
assert pi == 3

# Import a name that shadows the local
from math import pi as pi

# `pi` is now bound to math.pi, not the integer 3
assert pi != 3
assert abs(pi - 3.14159265358979) < 1e-9

# Rebind via a different import path
import math
assert math.pi is pi

# Local reassignment overrides the import
pi = 3
assert pi == 3

# And the math module's value is unchanged
assert math.pi > 3.14
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         opt_state="deoptimized",
                         tags={"IC", "invalidation", "import", "shadow"}),
    ),
    T(
        name="modify_closure_cell_contents",
        category="metaprog_invalidation",
        description=(
            "A function's __closure__ cells are modified in place by "
            "external code, changing the captured value. Subsequent "
            "invocations must observe the new value. The JIT cannot "
            "inline the captured value as a constant."
        ),
        source='''\
def make_adder(n):
    def add(x):
        return x + n
    return add

f = make_adder(10)
assert f(5) == 15

# Inspect the closure
assert len(f.__closure__) == 1
cell = f.__closure__[0]
assert cell.cell_contents == 10

# Mutate the cell directly
cell.cell_contents = 100
assert f(5) == 105

# Mutate again, including type change.
# add(x) returns x + n where n is the cell value, so f("cd") = "cd" + "ab"
cell.cell_contents = "ab"
assert f("cd") == "cdab"

# Mutate to a list (list + list concatenation)
# add(x) returns x + n, so f([3, 4]) = [3, 4] + [1, 2]
cell.cell_contents = [1, 2]
assert f([3, 4]) == [3, 4, 1, 2]

# Restore
cell.cell_contents = 10
assert f(5) == 15
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         call_behavior="closure", opt_state="deoptimized",
                         tags={"invalidation", "closure", "cell-mutation"}),
    ),
    T(
        name="exec_defines_then_call",
        category="metaprog_invalidation",
        description=(
            "exec() is used to define functions and classes in a fresh "
            "namespace. The defined objects are then retrieved and "
            "invoked. The JIT cannot have any precompiled cache for "
            "objects that did not exist when the surrounding code was "
            "compiled."
        ),
        source='''\
ns = {}
code = """
def greet(name):
    return f'hello, {name}!'

class Counter:
    def __init__(self):
        self.n = 0
    def inc(self):
        self.n += 1
        return self.n
"""
exec(code, ns)

greet = ns['greet']
Counter = ns['Counter']

assert greet('world') == 'hello, world!'

c = Counter()
assert c.inc() == 1
assert c.inc() == 2
assert c.inc() == 3

# Add more to the namespace and call immediately
exec('VALUE = 42', ns)
assert ns['VALUE'] == 42

exec('def double(x): return x * 2', ns)
assert ns['double'](21) == 42

# Define a class that inherits from the previously-defined Counter
exec('class LoudCounter(Counter):\\n    def inc(self):\\n        return super().inc() * 10', ns)
lc = ns['LoudCounter']()
assert lc.inc() == 10
assert lc.inc() == 20
assert lc.inc() == 30
''',
        tags=TagSet.make("stress", type_stability="bimorphic",
                         call_behavior="indirect", opt_state="deoptimized",
                         tags={"invalidation", "exec", "dynamic-def"}),
    ),
]
