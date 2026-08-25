# -*- coding: utf-8 -*-
# test_id: fuzz-state-00000024
# category: fuzz_state
# semantic: interpreter_tiers
# type_stability: polymorphic
# control_flow: loop
# call_behavior: direct
# opt_state: deoptimized
# tags: ['OSR', 'deoptimization', 'fuzz', 'perturb_change_global', 'seq_3', 'state']
def fact(n):
    if n <= 1:
        return 1
    return n * fact(n - 1)
def main():
    return fact(20)

