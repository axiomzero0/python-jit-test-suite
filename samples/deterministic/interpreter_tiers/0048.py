# -*- coding: utf-8 -*-
# test_id: tier-0000048
# category: interpreter_tiers
# semantic: interpreter_tiers
# type_stability: monomorphic
# control_flow: loop
# call_behavior: direct
# opt_state: hot
# tags: ['OSR', 'deoptimization', 'interp_to_opt', 'tier-transition']
try:
    i = 0
    while i < 100:
        if i == 50:
            raise ValueError('mid-loop')
        i += 1
except ValueError:
    pass

