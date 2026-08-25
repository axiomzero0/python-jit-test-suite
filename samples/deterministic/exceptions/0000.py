# -*- coding: utf-8 -*-
# test_id: exc-0000000
# category: exceptions
# semantic: exceptions
# type_stability: monomorphic
# control_flow: if_else
# call_behavior: direct
# opt_state: cold
# tags: ['deoptimization', 'exception', 'try_except']
try:
    raise ValueError('x')
except ValueError as e:
    assert str(e) == 'x'

