# -*- coding: utf-8 -*-
# test_id: fuzz-state-00000049
# category: fuzz_state
# semantic: interpreter_tiers
# type_stability: polymorphic
# control_flow: loop
# call_behavior: direct
# opt_state: hot
# tags: ['OSR', 'deoptimization', 'fuzz', 'perturb_raise_runtime_error', 'seq_1', 'state']
def make():
    x = [0]
    def f():
        x[0] += 1
        return x[0]
    return f
def main():
    f = make()
    s = 0
    for _ in range(100):
        s += f()
    return s

