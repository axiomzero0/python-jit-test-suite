# -*- coding: utf-8 -*-
# stress test: ic_method_add_to_base
# category: inline_caches
#
# Target: Call site `o.f()` is cached with A.f. Then a method `f` is added to base class B (parent of A). The IC must invalidate and pick up B.f for instances of B.
#
# Tags: ['IC', 'hierarchy', 'invalidation']
class B: pass
class A(B):
    def f(self): return 1

def call_f(o):
    return o.f()

a = A()
for _ in range(1000):
    assert call_f(a) == 1

# Now add f to B
B.f = lambda self: 99

b = B()
assert call_f(b) == 99

# A.f should still win for A instances (MRO: A comes before B)
assert call_f(a) == 1

