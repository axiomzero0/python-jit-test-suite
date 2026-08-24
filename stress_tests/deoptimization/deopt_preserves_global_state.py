# -*- coding: utf-8 -*-
# stress test: deopt_preserves_global_state
# category: deoptimization
# opt_state: (runs across all 6 states)
#
# Target: Deopt in a function that mutates a global. The global must reflect all mutations done before deopt.
#
# Tags: ['deopt', 'global', 'state']
G = [0]

def work():
    for i in range(1000):
        G[0] += i
        if i == 500:
            G[0] += 0.5  # deopt
    return G[0]

r = work()
assert r == sum(range(1000)) + 0.5
assert G[0] == r

