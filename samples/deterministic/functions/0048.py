# -*- coding: utf-8 -*-
# test_id: fn-0000048
# category: functions
# semantic: functions
# type_stability: monomorphic
# control_flow: straight_line
# call_behavior: direct
# opt_state: cold
# tags: ['function', 'nonlocal']
def make_counter():
    c = 0
    def step():
        nonlocal c
        c += 1
        return c
    return step
s = make_counter()
assert s() == 1 and s() == 2 and s() == 3

