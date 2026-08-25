# -*- coding: utf-8 -*-
# test_id: fuzz-ast-00000018
# category: fuzz_ast
# semantic: language_semantics
# type_stability: unknown
# control_flow: straight_line
# call_behavior: direct
# opt_state: hot
# tags: ['ast', 'fuzz', 'generated']
def main():
    x = 1000
    y = 0
    z = -100
    a = [0, 1, 2, 3, 4]
    b = [5, 6, 7, 8, 9]
    return {not ~((None < 0.0) * (None if 0 else True)) % min((1 if True else -100) or ('' or 2)): y}
