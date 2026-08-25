# -*- coding: utf-8 -*-
# test_id: fuzz-diff-00000015
# category: fuzz_differential
# semantic: language_semantics
# type_stability: unknown
# control_flow: straight_line
# call_behavior: direct
# opt_state: warm
# tags: ['CPython-vs-JIT', 'differential', 'fuzz']
def main():
    d = {i: i*i for i in range(10)}
    return d.get(5, -1) + d.get(99, -1)

