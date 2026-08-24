# -*- coding: utf-8 -*-
# test_id: fuzz-diff-00000013
# category: fuzz_differential
# semantic: language_semantics
# type_stability: unknown
# control_flow: straight_line
# call_behavior: direct
# opt_state: deoptimized
# tags: ['CPython-vs-JIT', 'differential', 'fuzz']
class A:
    x = 1
def main():
    a = A()
    v1 = a.x
    A.x = 2
    v2 = a.x
    return (v1, v2)

