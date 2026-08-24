# -*- coding: utf-8 -*-
# stress test: cycle_with_finalizer_still_finalized
# category: gc_interaction
# opt_state: (runs across all 6 states)
#
# Target: Objects in a reference cycle that each have __del__ must still be finalized by the cyclic GC. A JIT that assumes 'cycle => no finalizer' would leak the objects (or skip their __del__).
#
# Tags: ['GC', 'cycle', 'finalizer']
import gc

class CyclicFinal:
    counter = 0
    def __init__(self):
        CyclicFinal.counter += 1
    def __del__(self):
        CyclicFinal.counter -= 1

def make_cycle():
    a = CyclicFinal()
    b = CyclicFinal()
    a.partner = b
    b.partner = a

gc.collect()
CyclicFinal.counter = 0
for _ in range(1000):
    make_cycle()

gc.collect()
assert CyclicFinal.counter == 0, (
    f"{CyclicFinal.counter} instances leaked; cycle finalizer did not run"
)

