# -*- coding: utf-8 -*-
# test_id: tier-0000022
# category: interpreter_tiers
# semantic: interpreter_tiers
# type_stability: monomorphic
# control_flow: loop
# call_behavior: direct
# opt_state: warm
# tags: ['OSR', 'deoptimization', 'interp_to_base', 'tier-transition']
g_state = [0]
for i in range(100):
    g_state[0] = i
assert g_state[0] == 99

