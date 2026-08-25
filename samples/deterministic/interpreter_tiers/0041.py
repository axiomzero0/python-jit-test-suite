# -*- coding: utf-8 -*-
# test_id: tier-0000041
# category: interpreter_tiers
# semantic: interpreter_tiers
# type_stability: monomorphic
# control_flow: loop
# call_behavior: direct
# opt_state: hot
# tags: ['OSR', 'deoptimization', 'interp_to_opt', 'tier-transition']
acc = []
for i in range(100):
    acc.append(i)
assert len(acc) == 100

