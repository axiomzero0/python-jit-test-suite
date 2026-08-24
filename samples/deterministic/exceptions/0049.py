# -*- coding: utf-8 -*-
# test_id: exc-0000049
# category: exceptions
# semantic: exceptions
# type_stability: monomorphic
# control_flow: if_else
# call_behavior: direct
# opt_state: warm
# tags: ['deoptimization', 'exception', 'finally_during_deopt']
ran_finally = False
def f():
    try:
        for i in range(100):
            if i == 50:
                raise RuntimeError()
    finally:
        global ran_finally
        ran_finally = True
try:
    f()
except RuntimeError:
    pass
assert ran_finally is True

