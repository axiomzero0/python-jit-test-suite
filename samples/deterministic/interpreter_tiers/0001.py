# -*- coding: utf-8 -*-
# test_id: tier-0000001
# category: interpreter_tiers
# semantic: interpreter_tiers
# type_stability: monomorphic
# control_flow: loop
# call_behavior: direct
# opt_state: cold
# tags: ['OSR', 'deoptimization', 'interp_only', 'tier-transition']
acc = []
for i in range(100):
    acc.append(i)
assert len(acc) == 100

