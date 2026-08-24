# -*- coding: utf-8 -*-
# test_id: cont-0000008
# category: containers
# semantic: containers
# type_stability: monomorphic
# control_flow: straight_line
# call_behavior: direct
# opt_state: hot
# tags: ['alias_shallow', 'append', 'container', 'list']
x = []
for i in range(100):
    x.append(i)
assert len(x) == 100 and x[0] == 0 and x[-1] == 99

a = [1, 2]
b = a
b.append(3)
assert a == [1, 2, 3]

