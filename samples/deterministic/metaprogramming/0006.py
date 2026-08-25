# -*- coding: utf-8 -*-
# test_id: meta-0000006
# category: metaprogramming
# semantic: metaprogramming
# type_stability: megamorphic
# control_flow: straight_line
# call_behavior: indirect
# opt_state: cold
# tags: ['IC-miss', 'exec', 'metaprogramming']
ns = {}
exec('x = 42', ns)
assert ns['x'] == 42

