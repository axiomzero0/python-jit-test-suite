# -*- coding: utf-8 -*-
# stress test: live_range_split_at_back_edge
# category: register_alloc
#
# Target: A loop-carried variable is live across the loop back-edge. The allocator may choose to split its live range at the back-edge (spill at the end of the body, reload at the top). A buggy splitter that didn't account for the back-edge would either lose the value between iterations or keep it pinned in a register, blocking other allocations.
#
# Tags: ['back-edge', 'live-range-splitting', 'loop-carried', 'register-alloc']
def work(n):
    total = 0
    i = 0
    while i < n:
        # total and i are both loop-carried; both live across the
        # back-edge.
        total += i
        i += 1
    return total

assert work(100) == sum(range(100))
assert work(0) == 0
assert work(1) == 0
assert work(10) == 45
assert work(1000) == 499500

