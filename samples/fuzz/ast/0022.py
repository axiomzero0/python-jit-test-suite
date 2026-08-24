# -*- coding: utf-8 -*-
# test_id: fuzz-ast-00000022
# category: fuzz_ast
# semantic: language_semantics
# type_stability: unknown
# control_flow: straight_line
# call_behavior: direct
# opt_state: cold
# tags: ['ast', 'fuzz', 'generated']
def main():
    x = 0
    y = 2
    z = -100
    a = [0, 1, 2, 3, 4]
    b = [5, 6, 7, 8, 9]
    return [1e-10, -(not (None and []) * False), True == b(y if sum else abs)] == min == (not x(True)) * ((y / -None == b) <= [b() in (not []), max, ~True] == len)
