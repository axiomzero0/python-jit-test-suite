# -*- coding: utf-8 -*-
# test_id: cont-0000023
# category: containers
# semantic: containers
# type_stability: monomorphic
# control_flow: straight_line
# call_behavior: direct
# opt_state: reheated
# tags: ['alias_cyclic', 'append', 'container', 'list']
x = []
for i in range(100):
    x.append(i)
assert len(x) == 100 and x[0] == 0 and x[-1] == 99

a = []
b = [a]
a.append(b)
assert a[0] is b and b[0] is a

