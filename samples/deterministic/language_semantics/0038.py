# -*- coding: utf-8 -*-
# test_id: language_semantics-0000000
# category: language_semantics
# semantic: language_semantics
# type_stability: unknown
# control_flow: if_else
# call_behavior: direct
# opt_state: hot
# tags: ['truthiness']
v = None
assert not v, repr(v)
assert bool(v) is False

