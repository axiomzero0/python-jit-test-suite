# -*- coding: utf-8 -*-
# test_id: tier-0000004
# category: interpreter_tiers
# semantic: interpreter_tiers
# type_stability: monomorphic
# control_flow: loop
# call_behavior: direct
# opt_state: cold
# tags: ['OSR', 'deoptimization', 'interp_only', 'tier-transition']
for i in range(100):
    pass
assert True

