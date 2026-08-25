# -*- coding: utf-8 -*-
# test_id: obj-0000029
# category: objects
# semantic: objects
# type_stability: monomorphic
# control_flow: straight_line
# call_behavior: method
# opt_state: reheated
# tags: ['inline-cache', 'object-model', 'staticmethod']
class A:
    @staticmethod
    def f(x):
        return x * 2
assert A.f(21) == 42

