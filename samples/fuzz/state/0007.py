# -*- coding: utf-8 -*-
# test_id: fuzz-state-00000007
# category: fuzz_state
# semantic: interpreter_tiers
# type_stability: polymorphic
# control_flow: loop
# call_behavior: direct
# opt_state: reheated
# tags: ['OSR', 'deoptimization', 'fuzz', 'perturb_change_global', 'seq_6', 'state']
def fact(n):
    if n <= 1:
        return 1
    return n * fact(n - 1)
def main():
    return fact(20)

