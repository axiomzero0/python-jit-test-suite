# -*- coding: utf-8 -*-
# test_id: fuzz-diff-00000040
# category: fuzz_differential
# semantic: language_semantics
# type_stability: unknown
# control_flow: straight_line
# call_behavior: direct
# opt_state: very_hot
# tags: ['CPython-vs-JIT', 'differential', 'fuzz']
def main():
    x = []
    return x and 'truthy' or 'falsy'

