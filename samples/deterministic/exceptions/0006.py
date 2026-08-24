# -*- coding: utf-8 -*-
# test_id: exc-0000006
# category: exceptions
# semantic: exceptions
# type_stability: monomorphic
# control_flow: if_else
# call_behavior: direct
# opt_state: cold
# tags: ['deoptimization', 'exception', 'nested_try']
try:
    try:
        raise ValueError('inner')
    except KeyError:
        pass
except ValueError as e:
    assert str(e) == 'inner'

