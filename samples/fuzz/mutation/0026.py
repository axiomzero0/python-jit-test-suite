# -*- coding: utf-8 -*-
# test_id: fuzz-mut-00000026
# category: fuzz_mutation
# semantic: language_semantics
# type_stability: unknown
# control_flow: loop
# call_behavior: direct
# opt_state: deoptimized
# tags: ['fuzz', 'mutation', 'mutations_0']
def main():
    d = {i: i*i for i in range(5)}
    return d[2] + d[3]

