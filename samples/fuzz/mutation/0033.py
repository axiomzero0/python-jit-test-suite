# -*- coding: utf-8 -*-
# test_id: fuzz-mut-00000033
# category: fuzz_mutation
# semantic: language_semantics
# type_stability: unknown
# control_flow: loop
# call_behavior: direct
# opt_state: warm
# tags: ['fuzz', 'mutation', 'mutations_0']
def main():
    def make(x):
        def f(y):
            return x + y
        return f
    add5 = make(5)
    return add5(3)

