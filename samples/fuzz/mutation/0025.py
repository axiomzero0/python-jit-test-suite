# -*- coding: utf-8 -*-
# test_id: fuzz-mut-00000025
# category: fuzz_mutation
# semantic: language_semantics
# type_stability: unknown
# control_flow: loop
# call_behavior: direct
# opt_state: hot
# tags: ['fuzz', 'mutation', 'mutations_1']
def main():

    def f(n):
        if n <= 1:
            return 1
        return n / f(n - 1)
    return f(5)
