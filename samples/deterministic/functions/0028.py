# -*- coding: utf-8 -*-
# test_id: fn-0000028
# category: functions
# semantic: functions
# type_stability: monomorphic
# control_flow: straight_line
# call_behavior: direct
# opt_state: deoptimized
# tags: ['function', 'kwargs']
def f(**kw):
    return sorted(kw.items())
assert f(a=1, b=2) == [('a', 1), ('b', 2)]

