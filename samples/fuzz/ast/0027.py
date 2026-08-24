# -*- coding: utf-8 -*-
# test_id: fuzz-ast-00000027
# category: fuzz_ast
# semantic: language_semantics
# type_stability: unknown
# control_flow: straight_line
# call_behavior: direct
# opt_state: cold
# tags: ['ast', 'fuzz', 'generated']
def main():
    x = 2
    y = 1
    z = 1
    a = [0, 1, 2, 3, 4]
    b = [5, 6, 7, 8, 9]
    return (((-1 ** True or False * None or 7 >= False) or 'hello' or True ^ 2 == 2 < y if (b(False, 'abc') and +9223372036854775807 and (2147483647 not in 0)) + (9223372036854775807 * True > (1.0 if False else 'abc') is not b()) else ('' + True or 3.14 or x(42)) / (y / ('a' // 0))) != ([3.14 * 10000000000.0 != 42] < len())) < 2 < (x(b(z, {42: 1, []: 3.14, []: 'abc'} if None < [] == True else ['']), max) != min ** y)
