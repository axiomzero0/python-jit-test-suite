# -*- coding: utf-8 -*-
# test_id: fuzz-state-00000033
# category: fuzz_state
# semantic: interpreter_tiers
# type_stability: polymorphic
# control_flow: loop
# call_behavior: direct
# opt_state: warm
# tags: ['OSR', 'deoptimization', 'fuzz', 'perturb_trigger_gc', 'seq_1', 'state']
def g(n):
    for i in range(n):
        yield i * i
def main():
    return sum(g(100))

