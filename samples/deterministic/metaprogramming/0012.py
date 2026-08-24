# -*- coding: utf-8 -*-
# test_id: meta-0000012
# category: metaprogramming
# semantic: metaprogramming
# type_stability: megamorphic
# control_flow: straight_line
# call_behavior: indirect
# opt_state: cold
# tags: ['IC-miss', 'globals', 'metaprogramming']
def f():
    return list(globals().keys())
assert '__name__' in f()

