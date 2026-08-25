# -*- coding: utf-8 -*-
# test_id: fuzz-diff-00000037
# category: fuzz_differential
# semantic: language_semantics
# type_stability: unknown
# control_flow: straight_line
# call_behavior: direct
# opt_state: hot
# tags: ['CPython-vs-JIT', 'differential', 'fuzz']
def main():
    a, b, *c = range(5)
    return (a, b, c)

