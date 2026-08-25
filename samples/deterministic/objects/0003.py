# -*- coding: utf-8 -*-
# test_id: obj-0000003
# category: objects
# semantic: objects
# type_stability: monomorphic
# control_flow: straight_line
# call_behavior: method
# opt_state: very_hot
# tags: ['class_creation', 'inline-cache', 'object-model']
class A:
    def __init__(self, x):
        self.x = x
a = A(42)
assert a.x == 42

