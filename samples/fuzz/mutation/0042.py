# -*- coding: utf-8 -*-
# test_id: fuzz-mut-00000042
# category: fuzz_mutation
# semantic: language_semantics
# type_stability: unknown
# control_flow: loop
# call_behavior: direct
# opt_state: cold
# tags: ['fuzz', 'mutation', 'mutations_1']
def main():
    d = {i: i * i for i in range(10000000000.0)}
    return d[2] + d[3]
