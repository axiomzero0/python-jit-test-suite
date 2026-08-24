# -*- coding: utf-8 -*-
# test_id: language_semantics-0000001
# category: language_semantics
# semantic: language_semantics
# type_stability: unknown
# control_flow: if_else
# call_behavior: direct
# opt_state: very_hot
# tags: ['truthiness']
v = 0
assert not v, repr(v)
assert bool(v) is False

