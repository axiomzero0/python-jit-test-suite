# -*- coding: utf-8 -*-
# test_id: fuzz-ast-00000016
# category: fuzz_ast
# semantic: language_semantics
# type_stability: unknown
# control_flow: straight_line
# call_behavior: direct
# opt_state: cold
# tags: ['ast', 'fuzz', 'generated']
def main():
    x = 2147483647
    y = 2147483647
    z = 1000
    a = [0, 1, 2, 3, 4]
    b = [5, 6, 7, 8, 9]
    return -100 if 0 else min() // []
