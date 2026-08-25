# -*- coding: utf-8 -*-
# stress test: deopt_during_attribute_access
# category: deoptimization
#
# Target: JIT speculates `o.x` is an instance dict lookup at offset N. Then `o.x` becomes a property. Deopt must call the descriptor.
#
# Tags: ['attribute', 'deopt', 'descriptor']
class A:
    pass

a = A()
a.x = 1

def get(o):
    return o.x

for _ in range(1000):
    assert get(a) == 1

# Add a data descriptor with both __get__ and __set__ to the class.
# Data descriptors take priority over instance __dict__.
class Desc:
    def __get__(self, obj, owner):
        return 999
    def __set__(self, obj, value):
        pass  # no-op setter

A.x = Desc()
# Now a.x must return 999 (descriptor takes priority)
assert get(a) == 999

