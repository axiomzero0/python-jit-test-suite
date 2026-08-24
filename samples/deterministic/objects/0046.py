# -*- coding: utf-8 -*-
# test_id: obj-0000046
# category: objects
# semantic: objects
# type_stability: monomorphic
# control_flow: straight_line
# call_behavior: method
# opt_state: deoptimized
# tags: ['descriptor', 'inline-cache', 'object-model']
class Desc:
    def __get__(self, obj, owner):
        return 42
class A:
    v = Desc()
assert A().v == 42

