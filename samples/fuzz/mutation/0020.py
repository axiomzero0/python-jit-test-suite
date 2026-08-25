# -*- coding: utf-8 -*-
# test_id: fuzz-mut-00000020
# category: fuzz_mutation
# semantic: language_semantics
# type_stability: unknown
# control_flow: loop
# call_behavior: direct
# opt_state: warm
# tags: ['fuzz', 'mutation', 'mutations_1']
def main():
    x = 5
    if x > 1.5:
        return x * 2
    else:
        return x
