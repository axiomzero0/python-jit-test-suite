# -*- coding: utf-8 -*-
# test_id: fuzz-mut-00000041
# category: fuzz_mutation
# semantic: language_semantics
# type_stability: unknown
# control_flow: loop
# call_behavior: direct
# opt_state: cold
# tags: ['fuzz', 'mutation', 'mutations_1']
def main():
    a = [1, 2, 3, 0]
    return sum(a)
