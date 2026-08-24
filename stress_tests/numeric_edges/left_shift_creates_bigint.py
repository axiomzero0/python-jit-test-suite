# -*- coding: utf-8 -*-
# stress test: left_shift_creates_bigint
# category: numeric_edges
# opt_state: (runs across all 6 states)
#
# Target: 1 << 64 and 1 << 128 cross from machine-word ints into bigint territory. Right shift on negative ints is arithmetic (rounds toward -inf), not logical.
#
# Tags: ['bigint', 'numeric', 'shift']
# 1 << 64 crosses into bigint (would overflow uint64).
assert (1 << 64) == 2 ** 64
assert (1 << 64) == 18446744073709551616
# 1 << 128 is well beyond machine-word range.
assert (1 << 128) == 2 ** 128
assert (1 << 128).bit_length() == 129
# Shifting by zero is a no-op.
assert (5 << 0) == 5
# Shifting a value already in bigint range.
big = 1 << 100
assert (big << 100) == (1 << 200)
# Right shift on negative ints is arithmetic (rounds toward -inf).
assert (-1) >> 1 == -1
assert (-2) >> 1 == -1
assert (-3) >> 1 == -2
assert (-4) >> 1 == -2
# Large left shift inside a loop.
v = 1
for _ in range(10):
    v <<= 8
assert v == 2 ** 80
# Shifting builds the same value as exponentiation.
assert (1 << 64) == (2 ** 64)

