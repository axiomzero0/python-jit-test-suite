# -*- coding: utf-8 -*-
# test_id: meta-0000033
# category: metaprogramming
# semantic: metaprogramming
# type_stability: megamorphic
# control_flow: straight_line
# call_behavior: indirect
# opt_state: very_hot
# tags: ['IC-miss', 'metaprogramming', 'setattr']
class A: pass
a = A()
setattr(a, 'x', 42)
assert a.x == 42

