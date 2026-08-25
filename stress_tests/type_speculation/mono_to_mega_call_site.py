# -*- coding: utf-8 -*-
# stress test: mono_to_mega_call_site
# category: type_speculation
#
# Target: A call site `o.f()` is called with the same class for 1000 iterations, allowing the JIT to inline and emit a monomorphic inline cache. Then 6 different classes are passed, blowing past the megamorphic threshold. The IC must transition mono -> poly -> mega without losing any prior call results.
#
# Tags: ['IC', 'megamorphic']
class A:
    def f(self): return 1
class B:
    def f(self): return 2
class C:
    def f(self): return 3
class D:
    def f(self): return 4
class E:
    def f(self): return 5
class F:
    def f(self): return 6

def call(o):
    return o.f()

# Warm up monomorphic
s = 0
for _ in range(1000):
    s += call(A())

# Go megamorphic
objs = [A(), B(), C(), D(), E(), F()]
for o in objs * 100:
    s += call(o)

assert s == 1000 + sum(o.f() for o in objs) * 100

