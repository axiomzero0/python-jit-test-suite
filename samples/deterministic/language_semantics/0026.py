# -*- coding: utf-8 -*-
# test_id: language_semantics-0000002
# category: language_semantics
# semantic: language_semantics
# type_stability: unknown
# control_flow: loop
# call_behavior: direct
# opt_state: hot
# tags: ['comprehension', 'dict']
r = {i: i*i for i in range(5)}
assert r == {0:0, 1:1, 2:4, 3:9, 4:16}

