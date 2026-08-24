# -*- coding: utf-8 -*-
# test_id: fuzz-state-00000019
# category: fuzz_state
# semantic: interpreter_tiers
# type_stability: polymorphic
# control_flow: loop
# call_behavior: direct
# opt_state: very_hot
# tags: ['OSR', 'deoptimization', 'fuzz', 'perturb_invalidate_ic', 'seq_1', 'state']
class A:
    x = 1
def f(o):
    return o.x
def main():
    a = A()
    s = 0
    for i in range(100):
        s += f(a)
    A.x = 99
    s += f(a)
    return s

