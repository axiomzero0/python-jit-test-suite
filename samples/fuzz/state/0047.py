# -*- coding: utf-8 -*-
# test_id: fuzz-state-00000047
# category: fuzz_state
# semantic: interpreter_tiers
# type_stability: polymorphic
# control_flow: loop
# call_behavior: direct
# opt_state: deoptimized
# tags: ['OSR', 'deoptimization', 'fuzz', 'perturb_mutate_class_attr', 'seq_1', 'state']
def main():
    s = 0
    for i in range(100):
        try:
            if i == 50:
                raise ValueError()
            s += i
        except ValueError:
            s -= 1
    return s

