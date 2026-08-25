# -*- coding: utf-8 -*-
# test_id: obj-0000042
# category: objects
# semantic: objects
# type_stability: monomorphic
# control_flow: straight_line
# call_behavior: method
# opt_state: cold
# tags: ['descriptor', 'inline-cache', 'object-model']
class Desc:
    def __get__(self, obj, owner):
        return 42
class A:
    v = Desc()
assert A().v == 42

