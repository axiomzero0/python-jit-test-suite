# -*- coding: utf-8 -*-
# test_id: str-0000004
# category: strings
# semantic: strings
# type_stability: monomorphic
# control_flow: straight_line
# call_behavior: builtin
# opt_state: deoptimized
# tags: ['ascii', 'concat', 'string', 'unicode']
s = 'hello world'
assert (s + s) == s * 2

