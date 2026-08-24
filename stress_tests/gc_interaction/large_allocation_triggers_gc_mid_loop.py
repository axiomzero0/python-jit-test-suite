# -*- coding: utf-8 -*-
# stress test: large_allocation_triggers_gc_mid_loop
# category: gc_interaction
# opt_state: (runs across all 6 states)
#
# Target: Allocating large objects mid-loop can trigger an incremental GC or a full collection. The collection must not corrupt the in-progress computation: every list's contents must remain intact and reachable afterwards.
#
# Tags: ['GC', 'allocation', 'large-object']
import gc

gc.collect()
was_enabled = gc.isenabled()
gc.disable()
try:
    held = []
    totals = []
    for i in range(200):
        # ~40KB list per iteration; 200 of these pressure the GC.
        big = [j * i for j in range(5000)]
        if i % 2 == 0:
            held.append(big)
        totals.append(sum(big))
        # Manual GC mid-loop simulates the runtime's automatic trigger.
        if i % 50 == 49:
            gc.collect()
finally:
    if was_enabled:
        gc.enable()

assert len(held) == 100
assert all(t >= 0 for t in totals)
assert totals[0] == 0
assert totals[1] == sum(range(5000))
assert totals[-1] == 199 * sum(range(5000))
# Verify held lists are intact (GC did not recycle their storage).
for k, lst in enumerate(held):
    assert len(lst) == 5000
    assert lst[0] == 0
    assert lst[-1] == 4999 * (2 * k)

