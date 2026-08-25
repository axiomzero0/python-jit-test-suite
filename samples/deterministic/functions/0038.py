# -*- coding: utf-8 -*-
# test_id: fn-0000038
# category: functions
# semantic: functions
# type_stability: monomorphic
# control_flow: straight_line
# call_behavior: closure
# opt_state: hot
# tags: ['function', 'nested_closure']
def make(x):
    def make2(y):
        def f(z):
            return x + y + z
        return f
    return make2(10)
f = make(1)
assert f(100) == 111

