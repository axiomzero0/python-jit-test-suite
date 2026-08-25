# -*- coding: utf-8 -*-
# test_id: fuzz-diff-00000000
# category: fuzz_differential
# semantic: language_semantics
# type_stability: unknown
# control_flow: straight_line
# call_behavior: direct
# opt_state: cold
# tags: ['CPython-vs-JIT', 'differential', 'fuzz']
def main():
    x = 42
    return f'{x=}'

