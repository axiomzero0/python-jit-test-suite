# -*- coding: utf-8 -*-
# test_id: exc-0000030
# category: exceptions
# semantic: exceptions
# type_stability: monomorphic
# control_flow: if_else
# call_behavior: direct
# opt_state: cold
# tags: ['deoptimization', 'exc_in_function', 'exception']
def f(x):
    if x < 0:
        raise ValueError('negative')
    return x * 2
try:
    f(-1)
except ValueError:
    pass
assert f(5) == 10

