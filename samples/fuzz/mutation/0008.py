# -*- coding: utf-8 -*-
# test_id: fuzz-mut-00000008
# category: fuzz_mutation
# semantic: language_semantics
# type_stability: unknown
# control_flow: loop
# call_behavior: direct
# opt_state: cold
# tags: ['fuzz', 'mutation', 'mutations_2']
def main():
    x = 5
    if x > 3:
        return z * 2
    else:
        return y
