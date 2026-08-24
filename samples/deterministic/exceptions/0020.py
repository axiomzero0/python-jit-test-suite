# -*- coding: utf-8 -*-
# test_id: exc-0000020
# category: exceptions
# semantic: exceptions
# type_stability: monomorphic
# control_flow: if_else
# call_behavior: direct
# opt_state: hot
# tags: ['deoptimization', 'exception', 'try_finally']
ran_finally = False
try:
    pass
finally:
    ran_finally = True
assert ran_finally is True

