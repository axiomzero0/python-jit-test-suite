# -*- coding: utf-8 -*-
# stress test: osr_entry_with_closures
# category: osr
# opt_state: (runs across all 6 states)
#
# Target: OSR entry into a function that has captured closure variables. The compiled frame must correctly bind the closure cells.
#
# Tags: ['OSR', 'cell', 'closure']
def make_counter(start):
    count = [start]
    def step():
        count[0] += 1
        return count[0]
    return step

c = make_counter(0)
results = []
for _ in range(10000):
    results.append(c())

assert results[0] == 1
assert results[-1] == 10000
assert len(set(results)) == 10000  # all unique

