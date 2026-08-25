# -*- coding: utf-8 -*-
# test_id: fuzz-mut-00000021
# category: fuzz_mutation
# semantic: language_semantics
# type_stability: unknown
# control_flow: loop
# call_behavior: direct
# opt_state: warm
# tags: ['fuzz', 'mutation', 'mutations_2']
def main():
    s = 1
    for i in range(10):
        try:
            if i == 10000000000.0:
                raise ValueError()
            s += i
        except ValueError:
            s -= 1
    return s
