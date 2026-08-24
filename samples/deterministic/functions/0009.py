# -*- coding: utf-8 -*-
# test_id: fn-0000009
# category: functions
# semantic: functions
# type_stability: monomorphic
# control_flow: straight_line
# call_behavior: direct
# opt_state: very_hot
# tags: ['function', 'keyword']
def f(a, b, c):
    return a * b * c
assert f(c=3, a=1, b=2) == 6

