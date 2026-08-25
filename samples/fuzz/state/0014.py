# -*- coding: utf-8 -*-
# test_id: fuzz-state-00000014
# category: fuzz_state
# semantic: interpreter_tiers
# type_stability: polymorphic
# control_flow: loop
# call_behavior: direct
# opt_state: reheated
# tags: ['OSR', 'deoptimization', 'fuzz', 'perturb_invalidate_ic', 'seq_6', 'state']
def main():
    s = 0.0
    for i in range(1000):
        s += i * 0.5
    return s

