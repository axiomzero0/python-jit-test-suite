# -*- coding: utf-8 -*-
# test_id: tier-0000007
# category: interpreter_tiers
# semantic: interpreter_tiers
# type_stability: monomorphic
# control_flow: loop
# call_behavior: direct
# opt_state: cold
# tags: ['OSR', 'deoptimization', 'interp_only', 'tier-transition']
g_state = [0]
i = 0
while i < 100:
    g_state[0] = i
    i += 1
assert g_state[0] == 99

