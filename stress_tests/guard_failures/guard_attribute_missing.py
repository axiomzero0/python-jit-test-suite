# -*- coding: utf-8 -*-
# stress test: guard_attribute_missing
# category: guard_failures
# opt_state: (runs across all 6 states)
#
# Target: Attribute presence guard fails when attr is missing.
#
# Tags: ['attribute', 'guard', 'missing']
class A:
    def __init__(self):
        self.x = 1

a = A()

def get(o):
    return o.x

for _ in range(1000):
    get(a)

# Delete the attribute
del a.x
try:
    get(a)
    assert False
except AttributeError:
    pass

# Restore
a.x = 42
assert get(a) == 42

