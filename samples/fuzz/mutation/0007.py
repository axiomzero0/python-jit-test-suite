# -*- coding: utf-8 -*-
# test_id: fuzz-mut-00000007
# category: fuzz_mutation
# semantic: language_semantics
# type_stability: unknown
# control_flow: loop
# call_behavior: direct
# opt_state: warm
# tags: ['fuzz', 'mutation', 'mutations_3']
def main():
    z = 2147483648
    for i in range(100):
        x = x + i
    return x
