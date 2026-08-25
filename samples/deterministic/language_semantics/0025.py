# -*- coding: utf-8 -*-
# test_id: language_semantics-0000001
# category: language_semantics
# semantic: language_semantics
# type_stability: unknown
# control_flow: loop
# call_behavior: direct
# opt_state: warm
# tags: ['comprehension', 'set']
r = {i % 3 for i in range(10)}
assert r == {0, 1, 2}

