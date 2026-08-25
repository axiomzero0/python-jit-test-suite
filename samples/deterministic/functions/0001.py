# -*- coding: utf-8 -*-
# test_id: fn-0000001
# category: functions
# semantic: functions
# type_stability: monomorphic
# control_flow: straight_line
# call_behavior: direct
# opt_state: warm
# tags: ['function', 'positional']
def f(a, b, c):
    return a + b + c
assert f(1, 2, 3) == 6

