# -*- coding: utf-8 -*-
# stress test: guard_class_layout_change
# category: guard_failures
#
# Target: Class layout guard fails when a __slots__ attribute is added or removed.
#
# Tags: ['class', 'guard', 'layout', 'slots']
class A:
    __slots__ = ('x',)

a = A()
a.x = 1

def get(o):
    return o.x

for _ in range(1000):
    get(a)

# Subclass with different slots
class B(A):
    __slots__ = ('y',)

b = B()
b.x = 10
b.y = 20
assert get(b) == 10

