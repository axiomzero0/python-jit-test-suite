# -*- coding: utf-8 -*-
# stress test: escape_via_weakref_prevents_allocation_elimination
# category: gc_interaction
#
# Target: If the JIT's escape analysis sees an object only used locally it may eliminate the allocation. But if a weakref observes the object's identity, the allocation must survive: the weakref must see a distinct object per iteration.
#
# Tags: ['GC', 'escape-analysis', 'weakref']
import gc
import weakref

class Escapee:
    counter = 0
    def __init__(self):
        Escapee.counter += 1

def work():
    wrs = []
    for _ in range(1000):
        e = Escapee()
        # The weakref observes e's identity -> allocation cannot be
        # eliminated by escape analysis.
        wrs.append(weakref.ref(e))
    return wrs

Escapee.counter = 0
wrs = work()
assert Escapee.counter == 1000, (
    f"only {Escapee.counter} allocations; escape analysis wrongly elided"
)
gc.collect()
alive = sum(1 for r in wrs if r() is not None)
assert alive == 0, f"{alive} objects survived; lifetime extended past scope"

