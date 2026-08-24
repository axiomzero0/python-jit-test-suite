# -*- coding: utf-8 -*-
# stress test: closure_created_in_hot_loop
# category: closure_lifetime
# opt_state: (runs across all 6 states)
#
# Target: A hot loop creates a new closure on each iteration, each capturing a distinct value of the loop variable. The JIT must allocate a fresh cell per iteration and not collapse them into a shared cell (which would yield late binding).
#
# Tags: ['closure', 'hot-loop', 'per-iter-cell']
adders = []
for i in range(100):
    adders.append(lambda x, n=i: x + n)

# Each closure should add a distinct captured value
total = 0
for f in adders:
    total += f(10)
# 10 * 100 + sum(0..99) = 1000 + 4950 = 5950
assert total == 5950

# Spot check a few
assert adders[0](0) == 0
assert adders[50](0) == 50
assert adders[99](0) == 99

# Distinct cells, distinct objects
assert adders[0] is not adders[1]

