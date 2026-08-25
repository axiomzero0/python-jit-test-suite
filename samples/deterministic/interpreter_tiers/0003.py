# -*- coding: utf-8 -*-
# test_id: tier-0000003
# category: interpreter_tiers
# semantic: interpreter_tiers
# type_stability: monomorphic
# control_flow: loop
# call_behavior: direct
# opt_state: cold
# tags: ['OSR', 'deoptimization', 'interp_only', 'tier-transition']
try:
    for i in range(100):
        if i == 50:
            raise ValueError('mid-loop')
except ValueError:
    pass

