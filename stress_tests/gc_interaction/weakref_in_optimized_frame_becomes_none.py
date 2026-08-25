# -*- coding: utf-8 -*-
# stress test: weakref_in_optimized_frame_becomes_none
# category: gc_interaction
#
# Target: A weakref captured in an optimized frame must return None once the referent is collected. If the JIT keeps the referent alive via a hidden reference (e.g. in a register spilled to the frame), the weakref would incorrectly return a live object.
#
# Tags: ['GC', 'frame', 'weakref']
import gc
import weakref

class Resource:
    pass

def work():
    r = Resource()
    wr = weakref.ref(r)
    # Spin to encourage optimization; the JIT must not pin r across this loop.
    total = 0
    for _ in range(2000):
        total += 1
    assert wr() is not None, "referent must be alive during optimized frame"
    assert total == 2000
    return wr

wr = work()
gc.collect()
assert wr() is None, "weakref must return None after referent collected"

