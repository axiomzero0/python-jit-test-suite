# -*- coding: utf-8 -*-
# test_id: exc-0000044
# category: exceptions
# semantic: exceptions
# type_stability: monomorphic
# control_flow: if_else
# call_behavior: direct
# opt_state: hot
# tags: ['deoptimization', 'exc_during_deopt', 'exception']
def f(x):
    s = 0
    for i in range(100):
        if i == 50:
            raise ValueError('mid')
        s += i * x
    return s
try:
    f(2)
except ValueError:
    pass

