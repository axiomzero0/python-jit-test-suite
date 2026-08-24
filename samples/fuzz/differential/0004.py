# -*- coding: utf-8 -*-
# test_id: fuzz-diff-00000004
# category: fuzz_differential
# semantic: language_semantics
# type_stability: unknown
# control_flow: straight_line
# call_behavior: direct
# opt_state: warm
# tags: ['CPython-vs-JIT', 'differential', 'fuzz']
def main():
    def g():
        yield 1
        yield 2
        yield 3
    return list(g())

