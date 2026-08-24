# -*- coding: utf-8 -*-
# test_id: fuzz-state-00000025
# category: fuzz_state
# semantic: interpreter_tiers
# type_stability: polymorphic
# control_flow: loop
# call_behavior: direct
# opt_state: cold
# tags: ['OSR', 'deoptimization', 'fuzz', 'perturb_change_global', 'seq_1', 'state']
def main():
    x = []
    for i in range(1000):
        x.append(i)
    return sum(x)

