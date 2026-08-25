# -*- coding: utf-8 -*-
# test_id: str-0000006
# category: strings
# semantic: strings
# type_stability: monomorphic
# control_flow: straight_line
# call_behavior: builtin
# opt_state: cold
# tags: ['ascii', 'slice', 'string', 'unicode']
s = 'hello world'
assert s[1:3] == s[1:3]
assert s[::-1] == s[::-1]

