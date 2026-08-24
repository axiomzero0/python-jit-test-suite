# -*- coding: utf-8 -*-
# stress test: float_subnormal_min
# category: numeric_edges
# opt_state: (runs across all 6 states)
#
# Target: IEEE-754 subnormal numbers (smallest positive is ~5e-324). A JIT that flushes subnormals to zero would violate these assertions; halving the smallest subnormal must underflow to +0.0 while adding it to 1.0 must round away to 1.0.
#
# Tags: ['ieee-754', 'numeric', 'subnormal']
import math
import sys
# Smallest positive subnormal double: 2**-1074 (printed as 5e-324).
sub = 5e-324
assert sub == 2.0 ** -1074
assert sub > 0.0
# Halving it underflows to +0.0.
assert (sub / 2) == 0.0
# Adding to 0.0 is exact (no rounding).
assert (0.0 + sub) == sub
# But adding to 1.0 rounds away (sub is far below the ULP of 1.0).
assert (1.0 + sub) == 1.0
# Gradual underflow: smallest normal * eps == smallest subnormal.
assert (sys.float_info.min * sys.float_info.epsilon) == sub
# Multiplying two subnormals underflows to zero.
assert (sub * sub) == 0.0
# A JIT must not fold `0.0 < sub < sys.float_info.min` to False.
assert 0.0 < sub < sys.float_info.min

