# -*- coding: utf-8 -*-
# test_id: fuzz-ast-00000012
# category: fuzz_ast
# semantic: language_semantics
# type_stability: unknown
# control_flow: straight_line
# call_behavior: direct
# opt_state: hot
# tags: ['ast', 'fuzz', 'generated']
def main():
    x = 0
    y = 1000
    z = 7
    a = [0, 1, 2, 3, 4]
    b = [5, 6, 7, 8, 9]
    return a * b(z[b])
