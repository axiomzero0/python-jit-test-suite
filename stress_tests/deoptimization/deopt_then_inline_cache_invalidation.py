# -*- coding: utf-8 -*-
# stress test: deopt_then_inline_cache_invalidation
# category: deoptimization
#
# Target: Deopt and IC invalidation happen close together. The reconstructed frame must use the new IC, not the old stale cache.
#
# Tags: ['IC', 'deopt', 'invalidation']
class A:
    x = 1
class B(A):
    pass

def get(o):
    return o.x

b = B()
for _ in range(1000):
    assert get(b) == 1

# Add x to B (invalidates IC)
B.x = 99
assert get(b) == 99

# Trigger deopt in a different code path
def work():
    acc = 0
    for i in range(1000):
        if i == 500:
            acc += 0.5
        else:
            acc += i
    return acc

assert work() == sum(range(500)) + 0.5 + sum(range(501, 1000))

