# -*- coding: utf-8 -*-
# test_id: fuzz-ast-00000047
# category: fuzz_ast
# semantic: language_semantics
# type_stability: unknown
# control_flow: straight_line
# call_behavior: direct
# opt_state: cold
# tags: ['ast', 'fuzz', 'generated']
def main():
    x = 0
    y = 42
    z = 9223372036854775807
    a = [0, 1, 2, 3, 4]
    b = [5, 6, 7, 8, 9]
    return False / (([] if b({}) else ('abc' == 2147483647) <= -1.0 in -1.0) == z(x, None + [None])) if a[(not +(False & True)) <= (None and min()) == (not 1e-10)] else -1
