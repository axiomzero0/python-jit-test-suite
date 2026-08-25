# -*- coding: utf-8 -*-
# test_id: language_semantics-0000021
# category: language_semantics
# semantic: language_semantics
# type_stability: unknown
# control_flow: straight_line
# call_behavior: direct
# opt_state: very_hot
# tags: ['builtin', 'name-binding', 'walrus']
if (n := 10) > 5:
    assert n == 10

