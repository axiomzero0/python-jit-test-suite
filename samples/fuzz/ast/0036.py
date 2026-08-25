# -*- coding: utf-8 -*-
# test_id: fuzz-ast-00000036
# category: fuzz_ast
# semantic: language_semantics
# type_stability: unknown
# control_flow: straight_line
# call_behavior: direct
# opt_state: warm
# tags: ['ast', 'fuzz', 'generated']
def main():
    x = 0
    y = 1000
    z = 2
    a = [0, 1, 2, 3, 4]
    b = [5, 6, 7, 8, 9]
    return (a(y(True // True & {None: '', None: 10000000000.0, None: ''}, 10000000000.0), 2147483647) >= ((abs ^ [7, 1, None]) // (max and (3.14 or 1.0)) and 1000) > [[] > a(2) + ['hello'] != 'hello', [a << 9223372036854775807 + 'abc', abs(), 2 + -100 if -100 else 'hello' <= 1.0], +(10000000000.0 << 42) - (not 'hello')]) not in (((-100 / None != 9223372036854775807 / 2147483647 != (3.14 not in False)) / max[a] if 2147483647 else a) < {}) in (2147483647 in 0)
