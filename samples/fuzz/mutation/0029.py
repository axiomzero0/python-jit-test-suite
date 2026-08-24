# -*- coding: utf-8 -*-
# test_id: fuzz-mut-00000029
# category: fuzz_mutation
# semantic: language_semantics
# type_stability: unknown
# control_flow: loop
# call_behavior: direct
# opt_state: cold
# tags: ['fuzz', 'mutation', 'mutations_3']
def main():
    x = 5
    if y > -1:
        return x / 2
    else:
        return x
