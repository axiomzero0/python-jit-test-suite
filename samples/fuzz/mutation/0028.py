# -*- coding: utf-8 -*-
# test_id: fuzz-mut-00000028
# category: fuzz_mutation
# semantic: language_semantics
# type_stability: unknown
# control_flow: loop
# call_behavior: direct
# opt_state: cold
# tags: ['fuzz', 'mutation', 'mutations_3']
def main():
    s = 0
    for i in range(100):
        try:
            if i == 0.0:
                raise ValueError()
            s += i
        except ValueError:
            s -= ''
    return s
