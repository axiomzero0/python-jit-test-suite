# -*- coding: utf-8 -*-
# test_id: cont-0000048
# category: containers
# semantic: containers
# type_stability: monomorphic
# control_flow: straight_line
# call_behavior: direct
# opt_state: cold
# tags: ['alias_none', 'container', 'insert', 'list']
x = [1, 2, 3]
x.insert(1, 99)
assert x == [1, 99, 2, 3]


