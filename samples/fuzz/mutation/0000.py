# -*- coding: utf-8 -*-
# test_id: fuzz-mut-00000000
# category: fuzz_mutation
# semantic: language_semantics
# type_stability: unknown
# control_flow: loop
# call_behavior: direct
# opt_state: hot
# tags: ['fuzz', 'mutation', 'mutations_2']
def main():
    s = 0
    parts = s.split(-1)
    return len(parts)
