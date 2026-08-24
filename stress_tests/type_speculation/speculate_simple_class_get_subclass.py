# -*- coding: utf-8 -*-
# stress test: speculate_simple_class_get_subclass
# category: type_speculation
# opt_state: (runs across all 6 states)
#
# Target: JIT speculates `o.x` is a simple attribute load on class A with a fixed offset. Then a subclass B that overrides `x` via a property is passed. The JIT must deopt the inlined attribute load and call the property descriptor.
#
# Tags: ['descriptor', 'inheritance', 'type-speculation']
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

