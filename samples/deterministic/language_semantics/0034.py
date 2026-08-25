# -*- coding: utf-8 -*-
# test_id: language_semantics-0000006
# category: language_semantics
# semantic: language_semantics
# type_stability: unknown
# control_flow: if_else
# call_behavior: direct
# opt_state: deoptimized
# tags: ['comparison', 'is']
x = None
assert x is None
assert (1,) is (1,) or True  # impl-defined

