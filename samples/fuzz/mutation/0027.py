# -*- coding: utf-8 -*-
# test_id: fuzz-mut-00000027
# category: fuzz_mutation
# semantic: language_semantics
# type_stability: unknown
# control_flow: loop
# call_behavior: direct
# opt_state: cold
# tags: ['fuzz', 'mutation', 'mutations_2']
def main():
    s = ''
    for i in range(10):
        s += i / 2
    return s
