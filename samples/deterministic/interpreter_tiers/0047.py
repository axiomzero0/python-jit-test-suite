# -*- coding: utf-8 -*-
# test_id: tier-0000047
# category: interpreter_tiers
# semantic: interpreter_tiers
# type_stability: monomorphic
# control_flow: loop
# call_behavior: direct
# opt_state: hot
# tags: ['OSR', 'deoptimization', 'interp_to_opt', 'tier-transition']
g_state = [0]
i = 0
while i < 100:
    g_state[0] = i
    i += 1
assert g_state[0] == 99

