# -*- coding: utf-8 -*-
# test_id: fuzz-mut-00000047
# category: fuzz_mutation
# semantic: language_semantics
# type_stability: unknown
# control_flow: loop
# call_behavior: direct
# opt_state: hot
# tags: ['fuzz', 'mutation', 'mutations_2']
def main():
    y = 5
    if x > 3:
        return x * 7
    else:
        return x
