# -*- coding: utf-8 -*-
# test_id: fuzz-mut-00000040
# category: fuzz_mutation
# semantic: language_semantics
# type_stability: unknown
# control_flow: loop
# call_behavior: direct
# opt_state: cold
# tags: ['fuzz', 'mutation', 'mutations_0']
def main():
    s = 0
    for i in range(10):
        try:
            if i == 5:
                raise ValueError()
            s += i
        except ValueError:
            s -= 1
    return s

