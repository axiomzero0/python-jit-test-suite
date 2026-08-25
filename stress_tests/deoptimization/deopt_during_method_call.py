# -*- coding: utf-8 -*-
# stress test: deopt_during_method_call
# category: deoptimization
#
# Target: JIT inlines a method call. Then a subclass overrides the method. Deopt must re-dispatch through the MRO.
#
# Tags: ['deopt', 'method', 'override']
class Base:
    def f(self): return "base"

class Derived(Base):
    pass

def call(o):
    return o.f()

d = Derived()
for _ in range(1000):
    assert call(d) == "base"

# Override in Derived
Derived.f = lambda self: "derived"
assert call(d) == "derived"

