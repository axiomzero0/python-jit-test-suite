# -*- coding: utf-8 -*-
# stress test: ic_attribute_load_with_descriptor_added
# category: inline_caches
#
# Target: JIT caches `o.x` as a simple instance attribute load. Then a data descriptor `x` is added to the class, which should shadow the instance attribute. The IC must invalidate.
#
# Tags: ['IC', 'descriptor', 'invalidation']
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

