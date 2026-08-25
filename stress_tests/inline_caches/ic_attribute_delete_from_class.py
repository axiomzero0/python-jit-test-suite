# -*- coding: utf-8 -*-
# stress test: ic_attribute_delete_from_class
# category: inline_caches
#
# Target: Attribute `x` exists on the class, IC caches the lookup. Then the attribute is deleted from the class. The IC must invalidate and fall back to instance __dict__.
#
# Tags: ['IC', 'attribute-delete', 'invalidation']
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

