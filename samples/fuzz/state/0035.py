# -*- coding: utf-8 -*-
# test_id: fuzz-state-00000035
# category: fuzz_state
# semantic: interpreter_tiers
# type_stability: polymorphic
# control_flow: loop
# call_behavior: direct
# opt_state: hot
# tags: ['OSR', 'deoptimization', 'fuzz', 'perturb_raise_runtime_error', 'seq_1', 'state']
class A:
    def f(self):
        return 1
class B:
    def f(self):
        return 2
class C:
    def f(self):
        return 3
def g(o):
    return o.f()
def main():
    a, b, c = A(), B(), C()
    s = 0
    for i in range(100):
        s += g([a, b, c][i % 3])
    return s

