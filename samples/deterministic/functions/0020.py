# -*- coding: utf-8 -*-
# test_id: fn-0000020
# category: functions
# semantic: functions
# type_stability: monomorphic
# control_flow: straight_line
# call_behavior: direct
# opt_state: hot
# tags: ['args', 'function']
def f(*args):
    return sum(args)
assert f(1, 2, 3, 4) == 10

