# -*- coding: utf-8 -*-
# test_id: fuzz-ast-00000040
# category: fuzz_ast
# semantic: language_semantics
# type_stability: unknown
# control_flow: straight_line
# call_behavior: direct
# opt_state: warm
# tags: ['ast', 'fuzz', 'generated']
def main():
    x = 2
    y = 42
    z = 0
    a = [0, 1, 2, 3, 4]
    b = [5, 6, 7, 8, 9]
    return (a - (z() | -x) and abs(None, 'a') and +max([] % b(), min)) * 0.0
