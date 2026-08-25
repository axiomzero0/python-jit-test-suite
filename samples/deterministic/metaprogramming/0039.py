# -*- coding: utf-8 -*-
# test_id: meta-0000039
# category: metaprogramming
# semantic: metaprogramming
# type_stability: megamorphic
# control_flow: straight_line
# call_behavior: indirect
# opt_state: very_hot
# tags: ['IC-miss', 'delattr', 'metaprogramming']
class A: pass
a = A()
a.x = 5
delattr(a, 'x')
assert not hasattr(a, 'x')

