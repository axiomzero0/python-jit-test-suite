# -*- coding: utf-8 -*-
# test_id: tier-0000031
# category: interpreter_tiers
# semantic: interpreter_tiers
# type_stability: monomorphic
# control_flow: loop
# call_behavior: direct
# opt_state: warm
# tags: ['OSR', 'deoptimization', 'interp_to_base', 'tier-transition']
acc = []
for i in range(10):
    for j in range(10):
        acc.append(i)
assert len(acc) == 100

