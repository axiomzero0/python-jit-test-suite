# -*- coding: utf-8 -*-
# test_id: str-0000012
# category: strings
# semantic: strings
# type_stability: monomorphic
# control_flow: straight_line
# call_behavior: builtin
# opt_state: cold
# tags: ['ascii', 'search', 'string', 'unicode']
s = 'hello world'
assert ('l' in s) == ('l' in s)

