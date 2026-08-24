# -*- coding: utf-8 -*-
# test_id: obj-0000031
# category: objects
# semantic: objects
# type_stability: monomorphic
# control_flow: straight_line
# call_behavior: method
# opt_state: warm
# tags: ['classmethod', 'inline-cache', 'object-model']
class A:
    @classmethod
    def f(cls, x):
        return cls.__name__, x
assert A.f(7) == ('A', 7)

