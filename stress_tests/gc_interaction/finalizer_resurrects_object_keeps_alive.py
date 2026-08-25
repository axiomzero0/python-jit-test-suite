# -*- coding: utf-8 -*-
# stress test: finalizer_resurrects_object_keeps_alive
# category: gc_interaction
#
# Target: A __del__ that stores self into a global resurrects the object. The runtime must honor the new reference: a second GC pass must not collect the resurrected object. A JIT that finalized the object 'in place' without checking for resurrection would free memory still reachable from the global.
#
# Tags: ['GC', 'finalizer', 'resurrection']
import gc

resurrected = []

class Zombie:
    resurrect_allowed = True
    def __del__(self):
        if Zombie.resurrect_allowed:
            # Resurrect: create a new strong reference via the global list.
            resurrected.append(self)

def work():
    for _ in range(100):
        z = Zombie()

work()
gc.collect()
assert len(resurrected) == 100, (
    f"only {len(resurrected)} resurrected, expected 100"
)
# A second GC must not collect them: they are reachable from the global.
gc.collect()
assert len(resurrected) == 100, "resurrected objects collected prematurely"
# Verify they are still functional objects.
for z in resurrected:
    assert isinstance(z, Zombie)
# Disable resurrection so cleanup does not re-add objects.
Zombie.resurrect_allowed = False
resurrected.clear()
gc.collect()

