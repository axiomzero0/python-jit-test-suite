# -*- coding: utf-8 -*-
# test_id: language_semantics-0000000
# category: language_semantics
# semantic: language_semantics
# type_stability: unknown
# control_flow: straight_line
# call_behavior: direct
# opt_state: cold
# tags: ['assign', 'local', 'name-binding']
def f():
    x = 7
    return x
assert f() == 7

