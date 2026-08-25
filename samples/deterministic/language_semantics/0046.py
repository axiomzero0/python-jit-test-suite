# -*- coding: utf-8 -*-
# test_id: language_semantics-0000008
# category: language_semantics
# semantic: language_semantics
# type_stability: unknown
# control_flow: if_else
# call_behavior: direct
# opt_state: deoptimized
# tags: ['truthiness']
v = False
assert not v, repr(v)
assert bool(v) is False

