# -*- coding: utf-8 -*-
# test_id: meta-0000020
# category: metaprogramming
# semantic: metaprogramming
# type_stability: megamorphic
# control_flow: straight_line
# call_behavior: indirect
# opt_state: hot
# tags: ['IC-miss', 'locals', 'metaprogramming']
def f():
    x = 1
    loc = locals()
    return 'x' in loc
assert f() is True

