# -*- coding: utf-8 -*-
# test_id: str-0000049
# category: strings
# semantic: strings
# type_stability: monomorphic
# control_flow: straight_line
# call_behavior: builtin
# opt_state: warm
# tags: ['ascii', 'decode', 'string', 'unicode']
s = 'hello world'
b = s.encode('utf-8')
assert b.decode('utf-8') == s

