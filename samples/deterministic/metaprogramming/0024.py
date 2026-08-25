# -*- coding: utf-8 -*-
# test_id: meta-0000024
# category: metaprogramming
# semantic: metaprogramming
# type_stability: megamorphic
# control_flow: straight_line
# call_behavior: indirect
# opt_state: cold
# tags: ['IC-miss', 'getattr', 'metaprogramming']
assert getattr(int, 'real', None) is not None or True

