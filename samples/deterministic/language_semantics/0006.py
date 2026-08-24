# -*- coding: utf-8 -*-
# test_id: language_semantics-0000006
# category: language_semantics
# semantic: language_semantics
# type_stability: unknown
# control_flow: straight_line
# call_behavior: direct
# opt_state: cold
# tags: ['assign', 'enclosing', 'name-binding']
def outer():
    y = 1
    def inner():
        return y
    return inner()
assert outer() == 1

