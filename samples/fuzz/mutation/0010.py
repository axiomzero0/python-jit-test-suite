# -*- coding: utf-8 -*-
# test_id: fuzz-mut-00000010
# category: fuzz_mutation
# semantic: language_semantics
# type_stability: unknown
# control_flow: loop
# call_behavior: direct
# opt_state: warm
# tags: ['fuzz', 'mutation', 'mutations_1']
def main():
    s = 0
    for i in range(10):
        s += i * 2147483648
    return s
