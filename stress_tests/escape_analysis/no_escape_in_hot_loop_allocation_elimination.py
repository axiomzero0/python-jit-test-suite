# -*- coding: utf-8 -*-
# stress test: no_escape_in_hot_loop_allocation_elimination
# category: escape_analysis
# opt_state: (runs across all 6 states)
#
# Target: A loop allocates a fresh object every iteration; the object never escapes the iteration. A correct escape analysis can eliminate the allocation entirely (or fold the fields into scalars). A buggy analysis that did not track per-iteration lifetime would either keep allocating (missed optimization) or incorrectly merge state across iterations (wrong result).
#
# Tags: ['allocation-elimination', 'escape-analysis', 'loop', 'scalar-replacement']
class Acc:
    __slots__ = ("total",)
    def __init__(self):
        self.total = 0
    def add(self, x):
        self.total += x

def work(n):
    grand = 0
    for i in range(n):
        # Each Acc is local to this iteration; never escapes.
        a = Acc()
        a.add(i)
        a.add(i * 2)
        grand += a.total
    return grand

# i + 2i = 3i, so per-iteration total is 3*i.
expected = sum(3 * i for i in range(1000))
assert work(1000) == expected
assert work(0) == 0
assert work(1) == 0          # 3 * 0
assert work(2) == 3          # 3 * 0 + 3 * 1
assert work(10) == 3 * sum(range(10))

