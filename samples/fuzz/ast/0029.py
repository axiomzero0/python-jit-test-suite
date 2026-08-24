# -*- coding: utf-8 -*-
# test_id: fuzz-ast-00000029
# category: fuzz_ast
# semantic: language_semantics
# type_stability: unknown
# control_flow: straight_line
# call_behavior: direct
# opt_state: warm
# tags: ['ast', 'fuzz', 'generated']
def main():
    x = 2
    y = -100
    z = -100
    a = [0, 1, 2, 3, 4]
    b = [5, 6, 7, 8, 9]
    return ['', z({1.0 + 2 > abs(None, 3.14) or 10000000000.0 + (0 if 0.0 else 'abc'): 1.0, (not 'abc') / ({-10000000000.0: 0, True: True} / len): z, 0 * True / (0 | True) or min[-1.0]: abs(b if (True if True else 0) else min[0.0])})]
