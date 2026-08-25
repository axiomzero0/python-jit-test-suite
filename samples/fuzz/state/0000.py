# -*- coding: utf-8 -*-
# test_id: fuzz-state-00000000
# category: fuzz_state
# semantic: interpreter_tiers
# type_stability: polymorphic
# control_flow: loop
# call_behavior: direct
# opt_state: cold
# tags: ['OSR', 'deoptimization', 'fuzz', 'perturb_invalidate_ic', 'seq_1', 'state']
def main():
    s = 0
    for i in range(1000):
        s += i
    return s

