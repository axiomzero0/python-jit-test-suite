# -*- coding: utf-8 -*-
# test_id: tier-0000006
# category: interpreter_tiers
# semantic: interpreter_tiers
# type_stability: monomorphic
# control_flow: loop
# call_behavior: direct
# opt_state: cold
# tags: ['OSR', 'deoptimization', 'interp_only', 'tier-transition']
acc = []
i = 0
while i < 100:
    acc.append(i)
    i += 1
assert len(acc) == 100

