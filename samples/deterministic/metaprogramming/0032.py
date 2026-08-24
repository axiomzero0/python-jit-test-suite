# -*- coding: utf-8 -*-
# test_id: meta-0000032
# category: metaprogramming
# semantic: metaprogramming
# type_stability: megamorphic
# control_flow: straight_line
# call_behavior: indirect
# opt_state: hot
# tags: ['IC-miss', 'metaprogramming', 'setattr']
class A: pass
a = A()
setattr(a, 'x', 42)
assert a.x == 42

