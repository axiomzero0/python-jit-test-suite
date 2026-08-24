# -*- coding: utf-8 -*-
# test_id: tier-0000032
# category: interpreter_tiers
# semantic: interpreter_tiers
# type_stability: monomorphic
# control_flow: loop
# call_behavior: direct
# opt_state: warm
# tags: ['OSR', 'deoptimization', 'interp_to_base', 'tier-transition']
g_state = [0]
for i in range(10):
    for j in range(10):
        g_state[0] = i
assert g_state[0] == 99

