# -*- coding: utf-8 -*-
# stress test: ic_load_method_then_classmethod
# category: inline_caches
# opt_state: (runs across all 6 states)
#
# Target: JIT caches `o.f()` as a regular method call. Then `f` is rebound as a classmethod. The IC must invalidate and bind the class.
#
# Tags: ['IC', 'classmethod', 'invalidation']
class A:
    def f(self):
        return self

a = A()
def call(o):
    return o.f()

for _ in range(1000):
    assert call(a) is a

# Convert f to a classmethod
A.f = classmethod(lambda cls: cls)
assert call(a) is A

