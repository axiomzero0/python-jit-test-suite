# -*- coding: utf-8 -*-
# test_id: str-0000016
# category: strings
# semantic: strings
# type_stability: monomorphic
# control_flow: straight_line
# call_behavior: builtin
# opt_state: deoptimized
# tags: ['ascii', 'search', 'string', 'unicode']
s = 'hello world'
assert ('l' in s) == ('l' in s)

