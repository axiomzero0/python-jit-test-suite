# -*- coding: utf-8 -*-
# test_id: fuzz-mut-00000037
# category: fuzz_mutation
# semantic: language_semantics
# type_stability: unknown
# control_flow: loop
# call_behavior: direct
# opt_state: warm
# tags: ['fuzz', 'mutation', 'mutations_3']
def main():
    a = [False, 'x', 'x', 4]
    return sum(a)
