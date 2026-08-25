# -*- coding: utf-8 -*-
# stress test: suspended_generator_frame_cleaned_up
# category: gc_interaction
#
# Target: A generator suspended mid-iteration holds a frame with live locals. When the generator is dropped, GC must finalize the frame and release the locals. A JIT that pinned the frame for OSR would leak them.
#
# Tags: ['GC', 'frame', 'generator']
import gc

class Tracker:
    instances = 0
    def __init__(self):
        Tracker.instances += 1
    def __del__(self):
        Tracker.instances -= 1

def gen():
    t = Tracker()
    while True:
        yield t

# Create and start (but do not exhaust) many generators.
gens = [gen() for _ in range(100)]
for g in gens:
    next(g)

assert Tracker.instances == 100, "each generator should hold one Tracker"

# Drop all generator references; suspended frames must be cleaned up.
# `del g` releases the loop variable's hold on the last generator so GC
# can reclaim it (otherwise the test leaks exactly one frame).
del g
gens.clear()
gc.collect()
assert Tracker.instances == 0, (
    f"{Tracker.instances} trackers leaked from suspended generator frames"
)

