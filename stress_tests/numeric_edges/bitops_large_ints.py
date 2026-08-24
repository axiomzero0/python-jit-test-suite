# -*- coding: utf-8 -*-
# stress test: bitops_large_ints
# category: numeric_edges
# opt_state: (runs across all 6 states)
#
# Target: Bitwise operations on ints far larger than a machine word (2**100 | 2**200). A JIT that lowers these to native CPU instructions must fall back to bigint algorithms here.
#
# Tags: ['bigint', 'bitops', 'numeric']
a = 2 ** 100
b = 2 ** 200
# No overlapping bits -> OR is the sum, AND is zero.
assert (a | b) == (2 ** 100 + 2 ** 200)
assert (a & b) == 0
assert (b ^ a) == (2 ** 200 + 2 ** 100)
# Shifts.
assert (b >> 100) == (2 ** 100)
assert (a << 100) == (2 ** 200)
assert (2 ** 200 >> 200) == 1
# Bitwise NOT: ~x == -x - 1 (two's complement, arbitrary width).
assert ~a == -(2 ** 100) - 1
assert ~0 == -1
assert ~(-1) == 0
# bit_length.
assert a.bit_length() == 101
assert b.bit_length() == 201
assert (2 ** 100 - 1).bit_length() == 100
# Combine widely-spaced bits.
mask = 0
for i in (0, 64, 128, 200, 500):
    mask |= (1 << i)
assert mask.bit_length() == 501
assert mask == sum(1 << i for i in (0, 64, 128, 200, 500))

