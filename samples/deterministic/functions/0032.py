# -*- coding: utf-8 -*-
# test_id: fn-0000032
# category: functions
# semantic: functions
# type_stability: monomorphic
# control_flow: straight_line
# call_behavior: closure
# opt_state: hot
# tags: ['closure', 'function']
def make(x):
    def f(y):
        return x + y
    return f
add5 = make(5)
assert add5(3) == 8

