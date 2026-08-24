# -*- coding: utf-8 -*-
# stress test: ic_load_method_then_staticmethod
# category: inline_caches
# opt_state: (runs across all 6 states)
#
# Target: JIT caches `o.f()` as a bound method call. Then `f` is rebound as a staticmethod. The IC must invalidate and skip the binding step.
#
# Tags: ['IC', 'invalidation', 'staticmethod']
class A:
    def f(self):
        return self

a = A()
def call(o):
    return o.f()

for _ in range(1000):
    assert call(a) is a

A.f = staticmethod(lambda: 42)
assert call(a) == 42

