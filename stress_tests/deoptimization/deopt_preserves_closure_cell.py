# -*- coding: utf-8 -*-
# stress test: deopt_preserves_closure_cell
# category: deoptimization
# opt_state: (runs across all 6 states)
#
# Target: Deopt in a function with a captured closure variable. The closure cell must remain accessible after deopt.
#
# Tags: ['cell', 'closure', 'deopt']
def make():
    state = [0]
    def step(x):
        state[0] += x
        if x == 500:
            state[0] += 0.5  # deopt
        return state[0]
    return step

s = make()
results = []
for i in range(1000):
    results.append(s(i))

assert results[0] == 0
assert results[499] == sum(range(500))
assert results[500] == sum(range(501)) + 0.5
assert results[-1] == sum(range(1000)) + 0.5

