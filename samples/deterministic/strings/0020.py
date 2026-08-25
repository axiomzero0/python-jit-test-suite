# -*- coding: utf-8 -*-
# test_id: str-0000020
# category: strings
# semantic: strings
# type_stability: monomorphic
# control_flow: straight_line
# call_behavior: builtin
# opt_state: hot
# tags: ['ascii', 'replace', 'string', 'unicode']
s = 'hello world'
assert s.replace('l', 'L') == s.replace('l', 'L')

