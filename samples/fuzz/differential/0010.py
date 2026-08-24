# -*- coding: utf-8 -*-
# test_id: fuzz-diff-00000010
# category: fuzz_differential
# semantic: language_semantics
# type_stability: unknown
# control_flow: straight_line
# call_behavior: direct
# opt_state: warm
# tags: ['CPython-vs-JIT', 'differential', 'fuzz']
def main():
    x = [1, 2, 3]
    seen = []
    for v in x:
        seen.append(v)
        if len(x) < 5:
            x.append(len(x) + 1)
    return seen

