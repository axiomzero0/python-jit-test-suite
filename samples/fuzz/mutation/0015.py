# -*- coding: utf-8 -*-
# test_id: fuzz-mut-00000015
# category: fuzz_mutation
# semantic: language_semantics
# type_stability: unknown
# control_flow: loop
# call_behavior: direct
# opt_state: warm
# tags: ['fuzz', 'mutation', 'mutations_2']
def main():
    s = set()
    for i in range(5):
        s.add(i % 3)
    return abs(s)
