# -*- coding: utf-8 -*-
# stress test: reference_cycle_broken_by_gc
# category: gc_interaction
#
# Target: A reference cycle created in optimized code cannot be collected by refcounting alone. The cyclic GC must break the cycle and finalize each participant. If the JIT elided the cycle-breaking safepoint, the objects would leak.
#
# Tags: ['GC', 'cycle', 'finalizer']
import gc

class A:
    count = 0
    def __init__(self):
        A.count += 1
    def __del__(self):
        A.count -= 1

def make_cycle():
    a = A()
    b = A()
    a.partner = b
    b.partner = a
    # a <-> b cycle; neither is reachable once make_cycle returns.

A.count = 0
for _ in range(1000):
    make_cycle()

gc.collect()
assert A.count == 0, f"{A.count} instances leaked; cyclic GC did not break cycle"

