# -*- coding: utf-8 -*-
# test_id: fuzz-mut-00000003
# category: fuzz_mutation
# semantic: language_semantics
# type_stability: unknown
# control_flow: loop
# call_behavior: direct
# opt_state: cold
# tags: ['fuzz', 'mutation', 'mutations_0']
def main():
    s = 'hello world'
    return s.replace('l', 'L').upper()

