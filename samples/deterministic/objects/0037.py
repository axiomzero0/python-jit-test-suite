# -*- coding: utf-8 -*-
# test_id: obj-0000037
# category: objects
# semantic: objects
# type_stability: monomorphic
# control_flow: straight_line
# call_behavior: method
# opt_state: warm
# tags: ['inline-cache', 'object-model', 'property']
class A:
    def __init__(self):
        self._x = 0
    @property
    def x(self):
        return self._x
    @x.setter
    def x(self, v):
        self._x = v + 1
a = A()
a.x = 10
assert a.x == 11

