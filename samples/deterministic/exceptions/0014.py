# -*- coding: utf-8 -*-
# test_id: exc-0000014
# category: exceptions
# semantic: exceptions
# type_stability: monomorphic
# control_flow: if_else
# call_behavior: direct
# opt_state: hot
# tags: ['deoptimization', 'exception', 'try_else']
result = None
try:
    x = 1
except Exception:
    result = 'caught'
else:
    result = 'no_exc'
assert result == 'no_exc'

