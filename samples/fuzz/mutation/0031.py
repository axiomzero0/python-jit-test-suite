# -*- coding: utf-8 -*-
# test_id: fuzz-mut-00000031
# category: fuzz_mutation
# semantic: language_semantics
# type_stability: unknown
# control_flow: loop
# call_behavior: direct
# opt_state: warm
# tags: ['fuzz', 'mutation', 'mutations_1']
def main():
    s = 'abc,def,ghi'
    parts = s.split(0)
    return len(parts)
