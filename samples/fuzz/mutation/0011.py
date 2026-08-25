# -*- coding: utf-8 -*-
# test_id: fuzz-mut-00000011
# category: fuzz_mutation
# semantic: language_semantics
# type_stability: unknown
# control_flow: loop
# call_behavior: direct
# opt_state: deoptimized
# tags: ['fuzz', 'mutation', 'mutations_4']
def main():
    z = 1
    for i in range(''):
        x = x - i
    return z
