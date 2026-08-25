# -*- coding: utf-8 -*-
# test_id: tier-0000043
# category: interpreter_tiers
# semantic: interpreter_tiers
# type_stability: monomorphic
# control_flow: loop
# call_behavior: direct
# opt_state: hot
# tags: ['OSR', 'deoptimization', 'interp_to_opt', 'tier-transition']
try:
    for i in range(100):
        if i == 50:
            raise ValueError('mid-loop')
except ValueError:
    pass

