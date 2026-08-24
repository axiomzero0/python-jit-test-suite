# -*- coding: utf-8 -*-
# test_id: str-0000005
# category: strings
# semantic: strings
# type_stability: monomorphic
# control_flow: straight_line
# call_behavior: builtin
# opt_state: reheated
# tags: ['ascii', 'concat', 'string', 'unicode']
s = 'hello world'
assert (s + s) == s * 2

