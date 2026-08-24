# -*- coding: utf-8 -*-
# test_id: fuzz-mut-00000016
# category: fuzz_mutation
# semantic: language_semantics
# type_stability: unknown
# control_flow: loop
# call_behavior: direct
# opt_state: cold
# tags: ['fuzz', 'mutation', 'mutations_1']
def main():
    s = 0
    for i in range(10):
        s += i / 2
    return s
