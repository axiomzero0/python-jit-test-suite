# -*- coding: utf-8 -*-
# test_id: language_semantics-0000010
# category: language_semantics
# semantic: language_semantics
# type_stability: unknown
# control_flow: straight_line
# call_behavior: direct
# opt_state: deoptimized
# tags: ['enclosing', 'name-binding', 'nonlocal']
def make_counter():
    c = 0
    def step():
        nonlocal c
        c += 1
        return c
    return step
s = make_counter()
assert s() == 1 and s() == 2 and s() == 3

