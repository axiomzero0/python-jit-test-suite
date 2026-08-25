# -*- coding: utf-8 -*-
# test_id: fn-0000008
# category: functions
# semantic: functions
# type_stability: monomorphic
# control_flow: straight_line
# call_behavior: direct
# opt_state: hot
# tags: ['function', 'keyword']
def f(a, b, c):
    return a * b * c
assert f(c=3, a=1, b=2) == 6

