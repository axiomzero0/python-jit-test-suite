# -*- coding: utf-8 -*-
# test_id: meta-0000036
# category: metaprogramming
# semantic: metaprogramming
# type_stability: megamorphic
# control_flow: straight_line
# call_behavior: indirect
# opt_state: cold
# tags: ['IC-miss', 'delattr', 'metaprogramming']
class A: pass
a = A()
a.x = 5
delattr(a, 'x')
assert not hasattr(a, 'x')

