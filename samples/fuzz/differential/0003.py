# -*- coding: utf-8 -*-
# test_id: fuzz-diff-00000003
# category: fuzz_differential
# semantic: language_semantics
# type_stability: unknown
# control_flow: straight_line
# call_behavior: direct
# opt_state: warm
# tags: ['CPython-vs-JIT', 'differential', 'fuzz']
def main():
    a = [[0] * 3 for _ in range(3)]
    a[0][0] = 99
    return a[0][0] + a[1][0] + a[2][0]

