# -*- coding: utf-8 -*-
# test_id: language_semantics-0000001
# category: language_semantics
# semantic: language_semantics
# type_stability: unknown
# control_flow: straight_line
# call_behavior: direct
# opt_state: warm
# tags: ['aug_assign', 'local', 'name-binding']
x = 1
x += 2
x *= 3
x //= 2
x **= 2
x %= 5
assert x == ((1+2)*3//2)**2 % 5

