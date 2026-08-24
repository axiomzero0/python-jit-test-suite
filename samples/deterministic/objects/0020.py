# -*- coding: utf-8 -*-
# test_id: obj-0000020
# category: objects
# semantic: objects
# type_stability: monomorphic
# control_flow: straight_line
# call_behavior: method
# opt_state: hot
# tags: ['inline-cache', 'object-model', 'super_call']
class A:
    def __init__(self):
        self.x = 1
class B(A):
    def __init__(self):
        super().__init__()
        self.x += 1
b = B()
assert b.x == 2

