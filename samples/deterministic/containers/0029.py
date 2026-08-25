# -*- coding: utf-8 -*-
# test_id: cont-0000029
# category: containers
# semantic: containers
# type_stability: monomorphic
# control_flow: straight_line
# call_behavior: direct
# opt_state: reheated
# tags: ['alias_none', 'container', 'list', 'pop']
x = list(range(10))
assert x.pop() == 9
assert x.pop(0) == 0
assert len(x) == 8


