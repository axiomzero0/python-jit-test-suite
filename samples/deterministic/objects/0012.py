# -*- coding: utf-8 -*-
# test_id: obj-0000012
# category: objects
# semantic: objects
# type_stability: monomorphic
# control_flow: straight_line
# call_behavior: method
# opt_state: cold
# tags: ['inline-cache', 'multiple_inheritance', 'object-model']
class A:
    def f(self):
        return 1
class B:
    def g(self):
        return 2
class C(A, B):
    pass
c = C()
assert c.f() == 1 and c.g() == 2

