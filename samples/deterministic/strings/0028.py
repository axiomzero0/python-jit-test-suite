# -*- coding: utf-8 -*-
# test_id: str-0000028
# category: strings
# semantic: strings
# type_stability: monomorphic
# control_flow: straight_line
# call_behavior: builtin
# opt_state: deoptimized
# tags: ['ascii', 'split', 'string', 'unicode']
s = 'hello world'
parts = s.split(' ')
assert isinstance(parts, list)

