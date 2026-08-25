# -*- coding: utf-8 -*-
# stress test: py316_type_version_invalidation
# category: python_316_features
#
# Target: Type objects have version tags that change when the type's MRO or attribute layout changes. The JIT must invalidate any IC entries tied to a type version.
#
# Tags: ['IC', 'PEP-659', 'py3.16', 'type-version']
class A:
    x = 1

def get_x(o):
    return o.x

a = A()
for _ in range(1000):
    assert get_x(a) == 1

A.y = 99
assert a.y == 99
assert get_x(a) == 1

A.x = 100
assert get_x(a) == 100

class B(A):
    __slots__ = ("z",)

b = B()
b.z = 50
assert get_x(b) == 100
assert b.z == 50

