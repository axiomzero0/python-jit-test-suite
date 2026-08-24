# -*- coding: utf-8 -*-
# test_id: tier-0000029
# category: interpreter_tiers
# semantic: interpreter_tiers
# type_stability: monomorphic
# control_flow: loop
# call_behavior: direct
# opt_state: warm
# tags: ['OSR', 'deoptimization', 'interp_to_base', 'tier-transition']
i = 0
while i < 100:
    pass
    i += 1
assert True

