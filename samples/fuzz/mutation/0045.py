# -*- coding: utf-8 -*-
# test_id: fuzz-mut-00000045
# category: fuzz_mutation
# semantic: language_semantics
# type_stability: unknown
# control_flow: loop
# call_behavior: direct
# opt_state: deoptimized
# tags: ['fuzz', 'mutation', 'mutations_2']
def main():
    d = {i: i * i for i in range(7)}
    return d[2] / d[3]
