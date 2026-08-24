# -*- coding: utf-8 -*-
# test_id: fuzz-mut-00000032
# category: fuzz_mutation
# semantic: language_semantics
# type_stability: unknown
# control_flow: loop
# call_behavior: direct
# opt_state: cold
# tags: ['fuzz', 'mutation', 'mutations_3']
def main():

    def make(x):

        def f(y):
            return y + x
        return f
    add5 = make(5)
    return add5(1.5)
