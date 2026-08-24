# -*- coding: utf-8 -*-
# stress test: weakref_callback_sees_consistent_state
# category: gc_interaction
# opt_state: (runs across all 6 states)
#
# Target: A weakref callback fires during GC. At callback time the referent is already gone, so ref() must return None. If the JIT delays weakref clearing until after the slot is reused, the callback could see a different (recycled) object.
#
# Tags: ['GC', 'callback', 'weakref']
import gc
import weakref

class Obj:
    __slots__ = ("id", "__weakref__")

seen = []
def callback(ref):
    # Must observe None: the referent is dead by callback time.
    seen.append(ref() is None)

def work():
    wrs = []
    for i in range(1000):
        o = Obj()
        o.id = i
        # Keep the weakref alive so the callback fires when o is rebound.
        wrs.append(weakref.ref(o, callback))
    return wrs

wrs = work()
gc.collect()
assert len(seen) == 1000, f"only {len(seen)} callbacks fired"
assert all(seen), "callback observed non-None referent during GC"

