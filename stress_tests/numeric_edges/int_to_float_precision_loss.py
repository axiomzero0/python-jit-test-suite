# -*- coding: utf-8 -*-
# stress test: int_to_float_precision_loss
# category: numeric_edges
# opt_state: (runs across all 6 states)
#
# Target: Above 2**53 not all integers are representable as floats: float(2**53 + 1) == float(2**53). A JIT that widens int to float without checking the mantissa width would silently drop low bits.
#
# Tags: ['conversion', 'mantissa', 'numeric', 'precision']
# 2**53 is the boundary: above it, not all integers are representable.
assert 2 ** 53 == 9007199254740992
# 2**53 is exactly representable; 2**53 + 1 is NOT.
assert float(2 ** 53) == 9007199254740992.0
assert float(2 ** 53 + 1) == float(2 ** 53)    # the +1 is rounded away
assert float(2 ** 53 + 1) == 9007199254740992.0
assert float(2 ** 53 + 2) == 9007199254740994.0  # +2 survives (even)
# Round-trip int(float(x)) loses the low bit.
assert int(float(2 ** 53 + 1)) == 2 ** 53
assert int(float(2 ** 53 + 3)) == 2 ** 53 + 4    # rounds to nearest even
# Below 2**53 everything round-trips exactly.
for k in (0, 1, 2, 100, 2 ** 52, 2 ** 53 - 1):
    assert int(float(k)) == k
# Going much larger: the float skips many integers.
huge = 2 ** 70
assert float(huge + 1) == float(huge)            # +1 invisible at this scale
assert float(huge) + 1.0 == float(huge)         # adding 1.0 does nothing

