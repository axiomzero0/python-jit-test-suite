# -*- coding: utf-8 -*-
# test_id: language_semantics-0000003
# category: language_semantics
# semantic: language_semantics
# type_stability: unknown
# control_flow: loop
# call_behavior: direct
# opt_state: very_hot
# tags: ['comprehension', 'generator']
g = (i*i for i in range(5))
assert list(g) == [0, 1, 4, 9, 16]

