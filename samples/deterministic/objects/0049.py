# -*- coding: utf-8 -*-
# test_id: obj-0000049
# category: objects
# semantic: objects
# type_stability: monomorphic
# control_flow: if_else
# call_behavior: method
# opt_state: warm
# tags: ['getattribute', 'inline-cache', 'object-model']
class A:
    def __getattribute__(self, name):
        return 'X' if name == 'x' else super().__getattribute__(name)
a = A()
assert a.x == 'X'

