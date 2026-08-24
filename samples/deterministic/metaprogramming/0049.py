# -*- coding: utf-8 -*-
# test_id: meta-0000049
# category: metaprogramming
# semantic: metaprogramming
# type_stability: megamorphic
# control_flow: straight_line
# call_behavior: indirect
# opt_state: warm
# tags: ['IC-miss', 'dynamic_class', 'metaprogramming']
A = type('A', (), {'x': 1})
a = A()
assert a.x == 1

