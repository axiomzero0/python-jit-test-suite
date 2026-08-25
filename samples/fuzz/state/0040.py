# -*- coding: utf-8 -*-
# test_id: fuzz-state-00000040
# category: fuzz_state
# semantic: interpreter_tiers
# type_stability: polymorphic
# control_flow: loop
# call_behavior: direct
# opt_state: reheated
# tags: ['OSR', 'deoptimization', 'fuzz', 'perturb_trigger_gc', 'seq_1', 'state']
def main():
    x = []
    for i in range(1000):
        x.append(i)
    return sum(x)

