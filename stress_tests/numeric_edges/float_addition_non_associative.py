# -*- coding: utf-8 -*-
# stress test: float_addition_non_associative
# category: numeric_edges
#
# Target: Float addition is not associative: reordering operands changes the result. A JIT that reassociates sums for vectorization would change observable results; math.fsum and Kahan summation recover the correct total.
#
# Tags: ['associativity', 'fsum', 'ieee-754', 'numeric']
import math
# Reordering operands changes the result.
a, b, c = 1.0, 1e16, -1e16
left = (a + b) + c      # 1.0 is absorbed into 1e16, then cancels -> 0.0
right = a + (b + c)     # 1e16 + (-1e16) cancels exactly first -> 1.0
assert left == 0.0
assert right == 1.0
assert left != right
# A tiny addend is lost against a large value.
assert (1e16 + 1.0) == 1e16
assert (1e16 + 1.0) - 1e16 == 0.0
# Naive summation of 0.1 x10 drifts; math.fsum is correctly rounded.
naive = 0.0
for _ in range(10):
    naive += 0.1
assert naive != 1.0
assert naive == 0.9999999999999999
assert math.fsum([0.1] * 10) == 1.0
# Kahan compensated summation recovers the lost precision.
def kahan(values):
    total = 0.0
    comp = 0.0
    for v in values:
        y = v - comp
        t = total + y
        comp = (t - total) - y
        total = t
    return total
assert kahan([0.1] * 10) == 1.0
# Summation order over mixed magnitudes changes the total.
seq = [1e16, 1.0, -1e16, 1.0]
s_left_to_right = 0.0
for v in seq:
    s_left_to_right += v
# Pairing the 1e16 terms first cancels them exactly, leaving 1.0 + 1.0.
s_paired = (1e16 + (-1e16)) + (1.0 + 1.0)
assert s_left_to_right == 1.0
assert s_paired == 2.0
assert s_left_to_right != s_paired

