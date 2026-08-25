# -*- coding: utf-8 -*-
# test_id: language_semantics-0000000
# category: language_semantics
# semantic: language_semantics
# type_stability: unknown
# control_flow: loop
# call_behavior: direct
# opt_state: cold
# tags: ['comprehension', 'list']
r = [i*i for i in range(10) if i % 2 == 0]
assert r == [0, 4, 16, 36, 64]

