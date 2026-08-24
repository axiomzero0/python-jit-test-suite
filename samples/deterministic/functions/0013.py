# -*- coding: utf-8 -*-
# test_id: fn-0000013
# category: functions
# semantic: functions
# type_stability: monomorphic
# control_flow: straight_line
# call_behavior: direct
# opt_state: warm
# tags: ['defaults', 'function']
def f(a, b=2, c=3):
    return a + b + c
assert f(1) == 6 and f(1, 10) == 14 and f(1, 10, 100) == 111

