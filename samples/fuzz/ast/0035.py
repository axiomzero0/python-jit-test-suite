# -*- coding: utf-8 -*-
# test_id: fuzz-ast-00000035
# category: fuzz_ast
# semantic: language_semantics
# type_stability: unknown
# control_flow: straight_line
# call_behavior: direct
# opt_state: hot
# tags: ['ast', 'fuzz', 'generated']
def main():
    x = 7
    y = 9223372036854775807
    z = 2
    a = [0, 1, 2, 3, 4]
    b = [5, 6, 7, 8, 9]
    return (+'a' if y['a'] else [{None: [] and 1000}] != 3.14 > b + (False * False == (1.0 if 1e-10 else 42))) - (abs(not [False] not in (False == 1e-10 > '') == -100 - 'hello') if {a: y(3.14), 1000: x[-100], -None // max: 1 if sum() else len(3.14, 0)} ** sum else -1.0 >= min())
