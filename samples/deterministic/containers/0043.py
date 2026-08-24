# -*- coding: utf-8 -*-
# test_id: cont-0000043
# category: containers
# semantic: containers
# type_stability: monomorphic
# control_flow: straight_line
# call_behavior: direct
# opt_state: warm
# tags: ['alias_cyclic', 'container', 'list', 'pop']
x = list(range(10))
assert x.pop() == 9
assert x.pop(0) == 0
assert len(x) == 8

a = []
b = [a]
a.append(b)
assert a[0] is b and b[0] is a

