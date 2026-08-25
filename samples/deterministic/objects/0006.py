# -*- coding: utf-8 -*-
# test_id: obj-0000006
# category: objects
# semantic: objects
# type_stability: monomorphic
# control_flow: straight_line
# call_behavior: method
# opt_state: cold
# tags: ['inheritance', 'inline-cache', 'object-model']
class A:
    def f(self):
        return 1
class B(A):
    def g(self):
        return 2
b = B()
assert b.f() == 1 and b.g() == 2

