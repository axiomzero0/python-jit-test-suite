# -*- coding: utf-8 -*-
# test_id: fuzz-diff-00000030
# category: fuzz_differential
# semantic: language_semantics
# type_stability: unknown
# control_flow: straight_line
# call_behavior: direct
# opt_state: hot
# tags: ['CPython-vs-JIT', 'differential', 'fuzz']
def main():
    s = 0.0
    for i in range(100):
        s += i * 0.1
    return s

