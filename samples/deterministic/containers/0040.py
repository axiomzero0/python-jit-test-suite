# -*- coding: utf-8 -*-
# test_id: cont-0000040
# category: containers
# semantic: containers
# type_stability: monomorphic
# control_flow: straight_line
# call_behavior: direct
# opt_state: deoptimized
# tags: ['alias_nested', 'container', 'list', 'pop']
x = list(range(10))
assert x.pop() == 9
assert x.pop(0) == 0
assert len(x) == 8

a = [[1, 2], [3, 4]]
b = a[0]
b.append(99)
assert a[0] == [1, 2, 99]

