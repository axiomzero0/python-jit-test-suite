# -*- coding: utf-8 -*-
# test_id: fuzz-mut-00000023
# category: fuzz_mutation
# semantic: language_semantics
# type_stability: unknown
# control_flow: loop
# call_behavior: direct
# opt_state: cold
# tags: ['fuzz', 'mutation', 'mutations_1']
def main():
    s = 'abc,def,ghi'
    parts = s.split(1)
    return len(parts)
