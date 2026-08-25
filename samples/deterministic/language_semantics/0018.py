# -*- coding: utf-8 -*-
# test_id: language_semantics-0000018
# category: language_semantics
# semantic: language_semantics
# type_stability: unknown
# control_flow: straight_line
# call_behavior: direct
# opt_state: cold
# tags: ['assign', 'builtin', 'name-binding']
x = len
assert x([1,2,3]) == 3

