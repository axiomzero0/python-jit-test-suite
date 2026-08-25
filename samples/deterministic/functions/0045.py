# -*- coding: utf-8 -*-
# test_id: fn-0000045
# category: functions
# semantic: functions
# type_stability: monomorphic
# control_flow: straight_line
# call_behavior: direct
# opt_state: very_hot
# tags: ['function', 'late_binding']
fs = []
for i in range(3):
    fs.append(lambda: i)
# Late binding: all capture the last value of i
assert [f() for f in fs] == [2, 2, 2]

