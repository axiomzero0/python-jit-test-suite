# -*- coding: utf-8 -*-
# stress test: speculate_attribute_offset_then_add_slot
# category: type_speculation
#
# Target: JIT speculates `o.x` is at a fixed memory offset. Then the class is mutated (a __slots__ entry added or a new class attribute), invalidating the offset cache. The JIT must re-lookup the attribute.
#
# Tags: ['descriptor', 'slots', 'type-speculation']
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

