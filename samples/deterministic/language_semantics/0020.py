# -*- coding: utf-8 -*-
# test_id: language_semantics-0000020
# category: language_semantics
# semantic: language_semantics
# type_stability: unknown
# control_flow: straight_line
# call_behavior: direct
# opt_state: hot
# tags: ['builtin', 'name-binding', 'unpack']
a, b, c = 1, 2, 3
assert (a, b, c) == (1, 2, 3)

