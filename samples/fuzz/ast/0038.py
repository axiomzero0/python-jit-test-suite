# -*- coding: utf-8 -*-
# test_id: fuzz-ast-00000038
# category: fuzz_ast
# semantic: language_semantics
# type_stability: unknown
# control_flow: straight_line
# call_behavior: direct
# opt_state: warm
# tags: ['ast', 'fuzz', 'generated']
def main():
    x = 0
    y = 42
    z = -1
    a = [0, 1, 2, 3, 4]
    b = [5, 6, 7, 8, 9]
    return x + (([1000] and True not in (True * True and False % '' and z)) and sum(z) and (max[a[~9223372036854775807]] and (min and (not 1) + ('a' if 'abc' else True)) and ((True is True != 3.14) * a > -b)))
