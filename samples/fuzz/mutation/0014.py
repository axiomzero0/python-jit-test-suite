# -*- coding: utf-8 -*-
# test_id: fuzz-mut-00000014
# category: fuzz_mutation
# semantic: language_semantics
# type_stability: unknown
# control_flow: loop
# call_behavior: direct
# opt_state: cold
# tags: ['fuzz', 'mutation', 'mutations_1']
def main():

    def make(x):

        def f(y):
            return x + y
        return f
    add5 = make(5)
    return add5(0.0)
