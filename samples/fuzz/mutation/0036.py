# -*- coding: utf-8 -*-
# test_id: fuzz-mut-00000036
# category: fuzz_mutation
# semantic: language_semantics
# type_stability: unknown
# control_flow: loop
# call_behavior: direct
# opt_state: hot
# tags: ['fuzz', 'mutation', 'mutations_1']
def main():
    s = 100
    parts = s.split(',')
    return len(parts)
