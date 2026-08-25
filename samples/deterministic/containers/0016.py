# -*- coding: utf-8 -*-
# test_id: cont-0000016
# category: containers
# semantic: containers
# type_stability: monomorphic
# control_flow: straight_line
# call_behavior: direct
# opt_state: deoptimized
# tags: ['alias_nested', 'append', 'container', 'list']
x = []
for i in range(100):
    x.append(i)
assert len(x) == 100 and x[0] == 0 and x[-1] == 99

a = [[1, 2], [3, 4]]
b = a[0]
b.append(99)
assert a[0] == [1, 2, 99]

