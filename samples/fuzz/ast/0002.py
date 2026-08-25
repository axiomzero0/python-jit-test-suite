# -*- coding: utf-8 -*-
# test_id: fuzz-ast-00000002
# category: fuzz_ast
# semantic: language_semantics
# type_stability: unknown
# control_flow: straight_line
# call_behavior: direct
# opt_state: hot
# tags: ['ast', 'fuzz', 'generated']
def main():
    x = 1000
    y = -100
    z = 1000
    a = [0, 1, 2, 3, 4]
    b = [5, 6, 7, 8, 9]
    return False // ((len[True] != a <= 42 - 1000) - (a(42, 'hello') < 1 * None != (2 or False)) if (('hello' not in -100) == 10000000000.0 is not (False if 'a' else None)) >= (max(True) if not 0.0 else max()) > (min[[]] != max) else ('' or 9223372036854775807) * (2147483647 or 0 or '') >> len(+[], +1)) <= (y() and (z() or a([], abs()) or {sum: ([] if True else 'abc') ** b, ~'abc' or x: min[False - True]}) and a * (False in b))
