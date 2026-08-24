# -*- coding: utf-8 -*-
# test_id: meta-0000047
# category: metaprogramming
# semantic: metaprogramming
# type_stability: megamorphic
# control_flow: straight_line
# call_behavior: indirect
# opt_state: reheated
# tags: ['IC-miss', 'import_dynamic', 'metaprogramming']
import importlib
m = importlib.import_module('math')
assert hasattr(m, 'sqrt')

