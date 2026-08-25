# -*- coding: utf-8 -*-
# test_id: language_semantics-0000005
# category: language_semantics
# semantic: language_semantics
# type_stability: unknown
# control_flow: straight_line
# call_behavior: direct
# opt_state: reheated
# tags: ['global', 'local', 'name-binding']
g = 0
def set_g():
    global g
    g = 42
set_g()
assert g == 42

