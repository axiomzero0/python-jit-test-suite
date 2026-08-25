# -*- coding: utf-8 -*-
# test_id: str-0000040
# category: strings
# semantic: strings
# type_stability: monomorphic
# control_flow: straight_line
# call_behavior: builtin
# opt_state: deoptimized
# tags: ['ascii', 'format', 'string', 'unicode']
s = 'hello world'
assert ('{}').format() == '{}'
assert 'x' + s == 'x' + s

