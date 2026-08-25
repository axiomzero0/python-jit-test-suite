# -*- coding: utf-8 -*-
# stress test: float_precision_0_1_plus_0_2
# category: numeric_edges
#
# Target: The canonical IEEE-754 surprise: 0.1 + 0.2 != 0.3 in binary float, and accumulating 0.1 ten times drifts away from 1.0. A JIT that rewrites float sums must preserve IEEE rounding (or use math.fsum for correct rounding).
#
# Tags: ['ieee-754', 'numeric', 'precision', 'rounding']
import math
from decimal import Decimal
# The canonical surprise.
assert (0.1 + 0.2) != 0.3
assert (0.1 + 0.2) == 0.30000000000000004
# Decimal arithmetic is exact for decimal fractions.
assert Decimal('0.1') + Decimal('0.2') == Decimal('0.3')
# Accumulating 0.1 ten times does not yield exactly 1.0.
acc = 0.0
for _ in range(10):
    acc += 0.1
assert acc != 1.0
assert acc == 0.9999999999999999
# A tiny addend is lost against a large value.
assert (1e16 + 1.0) - 1e16 == 0.0
# math.fsum recovers the correctly-rounded sum.
assert math.fsum([0.1] * 10) == 1.0

