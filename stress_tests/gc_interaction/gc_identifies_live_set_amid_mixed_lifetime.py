# -*- coding: utf-8 -*-
# stress test: gc_identifies_live_set_amid_mixed_lifetime
# category: gc_interaction
# opt_state: (runs across all 6 states)
#
# Target: In a loop allocating many objects where some are kept alive via a list and others are not, the GC must correctly identify the live set. A JIT that confused the two sets (e.g. by sharing a backing store) would either leak dead objects or prematurely collect live ones.
#
# Tags: ['GC', 'live-set', 'weakref']
import gc
import weakref

class Item:
    __slots__ = ("idx", "__weakref__")

def work():
    kept = []
    dead_wrs = []
    for i in range(2000):
        it = Item()
        it.idx = i
        if i % 2 == 0:
            kept.append(it)
        else:
            dead_wrs.append(weakref.ref(it))
    return kept, dead_wrs

kept, dead_wrs = work()
gc.collect()

# Live set: exactly the 1000 kept items.
assert len(kept) == 1000
assert all(it.idx % 2 == 0 for it in kept)

# Dead set: every other object must be gone.
dead_alive = sum(1 for r in dead_wrs if r() is not None)
assert dead_alive == 0, f"{dead_alive} dead items survived GC"

# Now drop the kept list; those too must become collectible.
kept_wrs = [weakref.ref(it) for it in kept]
kept.clear()
gc.collect()
kept_alive = sum(1 for r in kept_wrs if r() is not None)
assert kept_alive == 0, f"{kept_alive} kept items survived after drop"

