# -*- coding: utf-8 -*-
# stress test: py316_inline_cache_values_array
# category: python_316_features
#
# Target: PEP 659: Inline caches use a values array for fast attribute access. Verify that the array is correctly invalidated when the type's attribute layout changes.
#
# Tags: ['PEP-659', 'inline-cache', 'py3.16', 'values-array']
class A:
    __slots__ = ("x", "y")

def get_x(o):
    return o.x

a = A()
a.x = 1
a.y = 2

for _ in range(1000):
    assert get_x(a) == 1

class B(A):
    __slots__ = ("z",)

b = B()
b.x = 10
b.y = 20
b.z = 30

assert get_x(b) == 10
assert b.z == 30
assert b.y == 20

