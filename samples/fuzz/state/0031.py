# -*- coding: utf-8 -*-
# test_id: fuzz-state-00000031
# category: fuzz_state
# semantic: interpreter_tiers
# type_stability: polymorphic
# control_flow: loop
# call_behavior: direct
# opt_state: deoptimized
# tags: ['OSR', 'deoptimization', 'fuzz', 'perturb_no_perturbation', 'seq_3', 'state']
def g(n):
    for i in range(n):
        yield i * i
def main():
    return sum(g(100))

