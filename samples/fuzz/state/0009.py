# -*- coding: utf-8 -*-
# test_id: fuzz-state-00000009
# category: fuzz_state
# semantic: interpreter_tiers
# type_stability: polymorphic
# control_flow: loop
# call_behavior: direct
# opt_state: deoptimized
# tags: ['OSR', 'deoptimization', 'fuzz', 'perturb_raise_runtime_error', 'seq_3', 'state']
def main():
    x = []
    for i in range(1000):
        x.append(i)
    return sum(x)

