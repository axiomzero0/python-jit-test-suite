# -*- coding: utf-8 -*-
# stress test: ic_attribute_watch_with_getattribute
# category: inline_caches
#
# Target: JIT caches `o.x`. Then the class gets a custom __getattribute__ that intercepts all attribute access. The IC must invalidate and route through the custom method.
#
# Tags: ['IC', 'getattribute', 'invalidation']
class A:
    x = 1

a = A()

def get_x(o):
    return o.x

for _ in range(1000):
    assert get_x(a) == 1

# Override __getattribute__
log = []
class B(A):
    def __getattribute__(self, name):
        log.append(name)
        return super().__getattribute__(name)

b = B()
assert get_x(b) == 1
assert "x" in log

