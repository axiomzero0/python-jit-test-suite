# -*- coding: utf-8 -*-
# test_id: fuzz-mut-00000024
# category: fuzz_mutation
# semantic: language_semantics
# type_stability: unknown
# control_flow: loop
# call_behavior: direct
# opt_state: cold
# tags: ['fuzz', 'mutation', 'mutations_1']
def main():
    s = 'hello world'
    return s.replace('l', 10000000000.0).upper()
