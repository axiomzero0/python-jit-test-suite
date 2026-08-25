# -*- coding: utf-8 -*-
# stress test: guard_function_arity
# category: guard_failures
#
# Target: JIT may inline a call assuming a fixed arity. If the callee is replaced with one of different arity, the guard fails.
#
# Tags: ['arity', 'call', 'guard']
def f(a, b):
    return a + b

def call(g, x, y):
    return g(x, y)

for _ in range(1000):
    call(f, 1, 2)

# Replace with a 3-arg function
def g3(a, b, c):
    return a + b + c

# call(f, 1, 2) was correct; now call(g3, 1, 2) should fail with TypeError
try:
    call(g3, 1, 2)
    assert False, "should raise TypeError"
except TypeError:
    pass

# Restore
assert call(f, 1, 2) == 3

