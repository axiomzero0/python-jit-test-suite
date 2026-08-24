# -*- coding: utf-8 -*-
# stress test: gc_during_deoptimization_completes_correctly
# category: gc_interaction
# opt_state: (runs across all 6 states)
#
# Target: GC triggered while a frame is being deoptimized must not corrupt the reconstructed interpreter state. The deopt handler reads object pointers from the compiled frame; if GC moves or frees one mid-reconstruction, the interpreter would see garbage.
#
# Tags: ['GC', 'deopt', 'safepoint']
import gc

class A:
    def f(self):
        return "a"

class B:
    def f(self):
        return "b"

def call(o):
    # Speculated monomorphic on A; deopt when B appears.
    return o.f()

# Warm up: A only.
a_pool = [A() for _ in range(500)]
for _ in range(3):
    for a in a_pool:
        assert call(a) == "a"

# Now interleave B (deopt trigger) with manual GC.
results = []
for i in range(1000):
    obj = B() if i % 2 == 0 else A()
    results.append(call(obj))
    if i % 50 == 0:
        gc.collect()

assert results.count("a") == 500
assert results.count("b") == 500
# Sanity: original A pool still works after all the deopt + GC churn.
for a in a_pool:
    assert call(a) == "a"

