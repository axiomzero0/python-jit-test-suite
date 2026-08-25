# -*- coding: utf-8 -*-
# test_id: fuzz-mut-00000030
# category: fuzz_mutation
# semantic: language_semantics
# type_stability: unknown
# control_flow: loop
# call_behavior: direct
# opt_state: hot
# tags: ['fuzz', 'mutation', 'mutations_0']
def main():
    try:
        x = 1 / 0
    except ZeroDivisionError:
        return -1
    return x

