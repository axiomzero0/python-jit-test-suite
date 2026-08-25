# -*- coding: utf-8 -*-
# stress test: deopt_preserves_int_sum_after_float
# category: deoptimization
#
# Target: Loop accumulates ints. On iteration 500, a float is added. Deopt must convert `acc` from a tagged int to a Python float object.
#
# Tags: ['deopt', 'int-to-float', 'unbox']
def work():
    acc = 0
    for i in range(1000):
        if i == 500:
            acc += 0.5
        else:
            acc += i
    return acc

r = work()
assert r == sum(range(500)) + 0.5 + sum(range(501, 1000))
assert isinstance(r, float)

