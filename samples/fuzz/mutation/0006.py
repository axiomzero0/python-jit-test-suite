# -*- coding: utf-8 -*-
# test_id: fuzz-mut-00000006
# category: fuzz_mutation
# semantic: language_semantics
# type_stability: unknown
# control_flow: loop
# call_behavior: direct
# opt_state: cold
# tags: ['fuzz', 'mutation', 'mutations_1']
def main():
    try:
        x = 1 / 1.5
    except ZeroDivisionError:
        return -1
    return x
