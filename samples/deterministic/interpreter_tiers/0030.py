# -*- coding: utf-8 -*-
# test_id: tier-0000030
# category: interpreter_tiers
# semantic: interpreter_tiers
# type_stability: monomorphic
# control_flow: loop
# call_behavior: direct
# opt_state: warm
# tags: ['OSR', 'deoptimization', 'interp_to_base', 'tier-transition']
for i in range(10):
    for j in range(10):
        print(i)

