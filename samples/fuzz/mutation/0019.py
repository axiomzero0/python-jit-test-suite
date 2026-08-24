# -*- coding: utf-8 -*-
# test_id: fuzz-mut-00000019
# category: fuzz_mutation
# semantic: language_semantics
# type_stability: unknown
# control_flow: loop
# call_behavior: direct
# opt_state: warm
# tags: ['fuzz', 'mutation', 'mutations_2']
def main():
    try:
        x = 1 * 1
    except ZeroDivisionError:
        return -1
    return x
