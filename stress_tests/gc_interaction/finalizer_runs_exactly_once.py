# -*- coding: utf-8 -*-
# stress test: finalizer_runs_exactly_once
# category: gc_interaction
#
# Target: An object with __del__ must have its finalizer called exactly once when collected. A JIT that double-frees the object (or fails to mark it as finalized before running the finalizer) would cause __del__ to run twice or zero times.
#
# Tags: ['GC', '__del__', 'finalizer']
import gc

class Finalized:
    counter = 0
    def __del__(self):
        Finalized.counter += 1

def work():
    for _ in range(1000):
        f = Finalized()
        # f rebound next iteration -> previous instance collected.

gc.collect()
work()
assert Finalized.counter == 1000, (
    f"finalizer ran {Finalized.counter} times, expected 1000"
)

