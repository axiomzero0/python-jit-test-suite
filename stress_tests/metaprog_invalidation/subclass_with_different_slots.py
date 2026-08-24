# -*- coding: utf-8 -*-
# stress test: subclass_with_different_slots
# category: metaprog_invalidation
# opt_state: (runs across all 6 states)
#
# Target: Subclasses of a slotted parent can add or omit slots, changing the instance memory layout. The JIT must respect the per-class layout when accessing slotted attributes.
#
# Tags: ['invalidation', 'layout', 'slots']
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

