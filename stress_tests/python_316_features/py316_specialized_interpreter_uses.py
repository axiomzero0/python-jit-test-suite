# -*- coding: utf-8 -*-
# stress test: py316_specialized_interpreter_uses
# category: python_316_features
#
# Target: PEP 659: Specialized adaptive interpreter. In 3.16, more bytecodes are specialized. Verify that specialization doesn't break observable behavior.
#
# Tags: ['PEP-659', 'adaptive', 'py3.16', 'specialization']
import sys

def hot_loop(n):
    s = 0
    for i in range(n):
        s += i
    return s

# Run enough times to trigger specialization
for _ in range(100):
    hot_loop(1000)

assert hot_loop(1000) == 499500
assert hot_loop(10000) == 49995000

def load_attr_test(obj):
    return obj.x

class A:
    def __init__(self):
        self.x = 42

a = A()
for _ in range(100):
    load_attr_test(a)

assert load_attr_test(a) == 42

