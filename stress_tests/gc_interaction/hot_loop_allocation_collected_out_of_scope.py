# -*- coding: utf-8 -*-
# stress test: hot_loop_allocation_collected_out_of_scope
# category: gc_interaction
#
# Target: Objects allocated in a hot loop and observed only via weakref must be collected as soon as the local is rebound. A JIT that extends the object's lifetime across iterations (e.g. by keeping a hidden register reference) would leave stale weakrefs alive.
#
# Tags: ['GC', 'lifetime', 'weakref']
import gc
import weakref

class Node:
    __slots__ = ("val", "__weakref__")

def hot_loop():
    wrs = []
    for i in range(2000):
        n = Node()
        n.val = i
        wrs.append(weakref.ref(n))
        # n is rebound next iteration; previous instance must die.
    return wrs

refs = hot_loop()
gc.collect()
alive = sum(1 for r in refs if r() is not None)
assert alive == 0, f"{alive} nodes survived GC; JIT may have extended lifetime"

