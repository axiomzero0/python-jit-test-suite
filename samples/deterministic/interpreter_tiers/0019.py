# -*- coding: utf-8 -*-
# test_id: tier-0000019
# category: interpreter_tiers
# semantic: interpreter_tiers
# type_stability: monomorphic
# control_flow: recursion
# call_behavior: recursive
# opt_state: cold
# tags: ['OSR', 'deoptimization', 'interp_only', 'tier-transition']
def rec(n, acc):
    if n <= 0:
        return acc
    pass
    return rec(n - 1, acc + 1)
acc = rec(100, 0)
assert acc == 100

