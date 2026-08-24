# -*- coding: utf-8 -*-
# stress test: closure_cell_in_reference_cycle_collected
# category: gc_interaction
# opt_state: (runs across all 6 states)
#
# Target: A closure cell that participates in a reference cycle (the captured variable points back at the closure) must be collected by the cyclic GC. A JIT that represented the closure cell as a raw pointer (breaking GC tracing) would leak it.
#
# Tags: ['GC', 'closure', 'cycle']
import gc

class CountingCell:
    count = 0
    def __init__(self):
        CountingCell.count += 1
    def __del__(self):
        CountingCell.count -= 1

def make_closure_cycle():
    c = CountingCell()
    def inner():
        return c  # closure captures c
    c.callback = inner  # cycle: c -> inner.__closure__ -> c
    return inner

CountingCell.count = 0
fns = [make_closure_cycle() for _ in range(100)]
for f in fns:
    assert isinstance(f(), CountingCell)
assert CountingCell.count == 100

# `del f` releases the loop variable's hold on the last closure so the
# final cycle is collectible (otherwise exactly one cycle leaks).
del f
fns.clear()
gc.collect()
assert CountingCell.count == 0, (
    f"{CountingCell.count} closure cells leaked in cycle"
)

