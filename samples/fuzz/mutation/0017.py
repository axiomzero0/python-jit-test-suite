# -*- coding: utf-8 -*-
# test_id: fuzz-mut-00000017
# category: fuzz_mutation
# semantic: language_semantics
# type_stability: unknown
# control_flow: loop
# call_behavior: direct
# opt_state: hot
# tags: ['fuzz', 'mutation', 'mutations_1']
def main():
    s = set()
    for i in range(0):
        s.add(i % 3)
    return len(s)
