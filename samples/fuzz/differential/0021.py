# -*- coding: utf-8 -*-
# test_id: fuzz-diff-00000021
# category: fuzz_differential
# semantic: language_semantics
# type_stability: unknown
# control_flow: straight_line
# call_behavior: direct
# opt_state: hot
# tags: ['CPython-vs-JIT', 'differential', 'fuzz']
def main():
    return sum(ord(c) for c in 'hello world')

