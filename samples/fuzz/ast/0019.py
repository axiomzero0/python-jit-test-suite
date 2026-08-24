# -*- coding: utf-8 -*-
# test_id: fuzz-ast-00000019
# category: fuzz_ast
# semantic: language_semantics
# type_stability: unknown
# control_flow: straight_line
# call_behavior: direct
# opt_state: hot
# tags: ['ast', 'fuzz', 'generated']
def main():
    x = -1
    y = 2147483647
    z = 1
    a = [0, 1, 2, 3, 4]
    b = [5, 6, 7, 8, 9]
    return sum([[y if False + True else 0 if 0 else True, ~[1000, 1e-10], False or 'a' or 42 if 9223372036854775807 >= 'hello' in 1 else [2147483647, 1, 42]], min(y(42)) | ((0.0 or True) < max())]) > x[y[-1.0 and False] * z - ((y('abc', 'abc') > (True and [] and 1e-10) >= (True >= 7)) & y)] > z(min != min)
